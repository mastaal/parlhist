"""
parlhist/parlhistnl/crawler/handeling.py

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
SPDX-FileCopyrightText: 2023-2024 Martijn Staal <parlhist [at] martijn-staal.nl>
SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import datetime
import logging
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from celery import shared_task
from celery.result import AsyncResult
from django.db.models import QuerySet

from parlhistnl.models import Handeling, Kamerstuk, KamerstukDossier

from parlhistnl.crawler.utils import (
    CrawlerException,
    get_url_or_error,
    koop_sru_api_request_all,
    retrieve_xml_element_text_or_fail,
    retrieve_xml_element_keyed_value_or_fail,
    shorten_kamer,
)
from parlhistnl.crawler.kamerstuk import crawl_kamerstuk
from parlhistnl.crawler.kamerdossier import crawl_kamerstukdossier

logger = logging.getLogger(__name__)


def __get_behandelde_kamerstukdossiers_and_kamerstukken(
    xml: ET.Element,
) -> dict[str, list[str]]:
    """Get the information of the related dossiers and kamerstukken (don't directly crawl them)"""

    behandeld_xml_matches = xml.findall("metadata[@name='OVERHEIDop.behandeldDossier']")

    logger.debug("Found %s", [x.get("content") for x in behandeld_xml_matches])

    # kamerstukken: list[Kamerstuk] = []
    # kamerstukdossiers: list[KamerstukDossier] = []
    kamerstukken: list[str] = []
    kamerstukdossiers: list[str] = []

    for xml_match in behandeld_xml_matches:
        # If it contains a semicolon, it is a kamerstuk (e.g., '35899;7', '35925-VII;31' or '35979;F'),
        # else, it is a dossier (e.g., '35873', or '35933', or '35925-VII').
        string_match = xml_match.get("content")
        if ";" in string_match:
            kamerstukken.append(string_match)
        else:
            kamerstukdossiers.append(string_match)

    return {
        "behandelde_kamerstukken": kamerstukken,
        "behandelde_kamerstukdossiers": kamerstukdossiers,
    }


def create_or_update_handeling_from_raw_metadata_and_content(
    identifier: str,
    sru_record: ET.Element,
    raw_metadata_xml: str,
    raw_html: str,
    raw_html_is_inner_html: bool,
    raw_xml: str,
) -> Handeling:
    """
    Create or update a Handeling from the raw metadata and raw html, either from new requests or from stored raw data

    Always updates if an existing Handeling.
    """

    logger.debug("Gathering information for %s", identifier)

    metadata_xml = ET.fromstring(raw_metadata_xml)

    creator_string = retrieve_xml_element_keyed_value_or_fail(
        metadata_xml, "metadata[@name='DC.creator']", "content"
    )
    kamer = shorten_kamer(creator_string)

    vergaderdatum_str = retrieve_xml_element_text_or_fail(
        sru_record, ".//overheidwetgeving:datumVergadering"
    )
    vergaderdatum = datetime.datetime.strptime(vergaderdatum_str, "%Y-%m-%d").date()

    vergaderjaar = retrieve_xml_element_keyed_value_or_fail(
        metadata_xml, "metadata[@name='OVERHEIDop.vergaderjaar']", "content"
    )

    titel = retrieve_xml_element_keyed_value_or_fail(
        metadata_xml, "metadata[@name='DC.title']", "content"
    )

    try:
        handelingtype = retrieve_xml_element_keyed_value_or_fail(
            metadata_xml,
            "metadata[@name='DC.type'][@scheme='OVERHEIDop.HandelingTypen']",
            "content",
        )
    except CrawlerException:
        # Some older Handeling items do not have this metadata, so we add our placeholder.
        handelingtype = "GEEN_HANDELINGTYPE_BEKEND"

    uncrawled = __get_behandelde_kamerstukdossiers_and_kamerstukken(metadata_xml)

    data = {"uncrawled": uncrawled}

    preferred_url = retrieve_xml_element_text_or_fail(sru_record, ".//gzd:preferredUrl")

    # Extract the text
    soup = BeautifulSoup(raw_html, "html.parser")
    if not raw_html_is_inner_html:
        elems = soup.select("article div#broodtekst.stuk.broodtekst-container")

        if len(elems) > 1:
            logger.info(
                "Got multiple matches where only one was expected %s", identifier
            )

        inner_html = str(elems[0])

        tekst = elems[0].get_text()
    else:
        tekst = soup.get_text()
        inner_html = raw_html

    handeling, _ = Handeling.objects.get_or_create(identifier=identifier)

    handeling.kamer = kamer
    handeling.vergaderdag = vergaderdatum
    handeling.vergaderjaar = vergaderjaar
    handeling.titel = titel
    handeling.handelingtype = handelingtype
    handeling.tekst = tekst
    handeling.raw_html = inner_html
    handeling.raw_xml = raw_xml
    handeling.raw_metadata_xml = raw_metadata_xml
    handeling.sru_record_xml = ET.tostring(sru_record)
    handeling.preferred_url = preferred_url
    handeling.data = data
    handeling.save()

    return handeling


def crawl_uncrawled_behandelde_kamerstukken(handeling: Handeling) -> list[Kamerstuk]:
    """
    Crawl behandelde Kamerstukken in a Handeling, and add the relevant relations in the database.
    """

    uncrawled_kamerstukken: list[str] = handeling.data["uncrawled"][
        "behandelde_kamerstukken"
    ]

    logger.info(
        "Crawling the following uncrawled behandelde kamerstukken %s",
        uncrawled_kamerstukken,
    )

    newly_added_kamerstukken: list[Kamerstuk] = []
    removable_uncrawled_behandelde_kamerstukken: list[str] = []

    for uncrawled_kamerstuk in uncrawled_kamerstukken:
        dossiernummer = uncrawled_kamerstuk.split(";")[0]
        ondernummer = uncrawled_kamerstuk.split(";")[1]

        try:
            kamerstuk = crawl_kamerstuk(dossiernummer, ondernummer)

            handeling.behandelde_kamerstukken.add(kamerstuk)

            newly_added_kamerstukken.append(kamerstuk)
            removable_uncrawled_behandelde_kamerstukken.append(uncrawled_kamerstuk)
        except CrawlerException as exc:
            logger.fatal(
                "Received crawler exception when crawling kst-%s, %s, skipping (%s)",
                dossiernummer,
                ondernummer,
                exc,
            )

    for removable_kamerstuk in removable_uncrawled_behandelde_kamerstukken:
        handeling.data["uncrawled"]["behandelde_kamerstukken"].remove(
            removable_kamerstuk
        )

    handeling.save()

    return newly_added_kamerstukken


def recrawl_behandelde_kamerstukken(handeling: Handeling) -> list[Kamerstuk]:
    """Recrawl behandelde kamerstukken"""

    kamerstukken: QuerySet[Kamerstuk] = handeling.behandelde_kamerstukken.all()

    for kamerstuk in kamerstukken:
        crawl_kamerstuk(
            kamerstuk.hoofddossier.dossiernummer, kamerstuk.ondernummer, update=True
        )

    return kamerstukken


def crawl_uncrawled_behandelde_kamerstukdossiers(
    handeling: Handeling,
) -> list[list[Kamerstuk]]:
    """Crawl behandelde kamerstukdossiers in a Handeling, and add the relevant relations in the database."""

    uncrawled_kamerstukdossiers: list[str] = handeling.data["uncrawled"][
        "behandelde_kamerstukdossiers"
    ]

    logger.info(
        "Crawling the following uncrawled behandelde kamerstukdossiers %s",
        uncrawled_kamerstukdossiers,
    )

    newly_added_kamerstukken: list[list[Kamerstuk]] = []
    removable_uncrawled_behandelde_kamerstukdossiers: list[str] = []

    for uncrawled_kamerstukdossier in uncrawled_kamerstukdossiers:
        try:
            crawled_kamerstukken = crawl_kamerstukdossier(uncrawled_kamerstukdossier)

            for crawled_kamerstuk in crawled_kamerstukken:
                handeling.behandelde_kamerstukken.add(crawled_kamerstuk)

            handeling.behandelde_kamerstukdossiers.add(
                crawled_kamerstukken[0].hoofddossier
            )

            newly_added_kamerstukken.append(crawled_kamerstukken)
            removable_uncrawled_behandelde_kamerstukdossiers.append(
                uncrawled_kamerstukdossier
            )
        except CrawlerException as exc:
            logger.fatal(
                "Received crawler exception while crawling kamerstukdossier %s, skipping (%s)",
                uncrawled_kamerstukdossier,
                exc,
            )

    for removable_kamerstukdossier in removable_uncrawled_behandelde_kamerstukdossiers:
        handeling.data["uncrawled"]["behandelde_kamerstukdossiers"].remove(
            removable_kamerstukdossier
        )

    handeling.save()

    return newly_added_kamerstukken


def recrawl_behandelde_kamerstukdossiers(handeling: Handeling) -> list[list[Kamerstuk]]:
    """Recrawl behandelde kamerstukdossiers"""

    kamerstukdossiers: QuerySet[KamerstukDossier] = (
        handeling.behandelde_kamerstukdossiers.all()
    )

    crawled_kamerstukken: list[list[Kamerstuk]] = []

    for kamerstukdossier in kamerstukdossiers:
        ksts = crawl_kamerstukdossier(
            kamerstukdossier.dossiernummer, update=True, ignore_failure=True
        )

        crawled_kamerstukken.append(ksts)

    return crawled_kamerstukken


def crawl_handeling_using_sru_record(sru_record: ET.Element) -> Handeling:
    """Crawl a Handeling using a KOOP SRU api record (parsed xml)"""

    identifier = retrieve_xml_element_text_or_fail(sru_record, ".//dcterms:identifier")

    logger.info("Crawling %s", identifier)

    preferred_url = retrieve_xml_element_text_or_fail(sru_record, ".//gzd:preferredUrl")
    html_url = retrieve_xml_element_text_or_fail(
        sru_record, ".//gzd:itemUrl[@manifestation='html']"
    )
    xml_url = retrieve_xml_element_text_or_fail(
        sru_record, ".//gzd:itemUrl[@manifestation='xml']"
    )
    metadata_xml_url = retrieve_xml_element_text_or_fail(
        sru_record, ".//gzd:itemUrl[@manifestation='metadata']"
    )

    html_response = get_url_or_error(preferred_url)
    metadata_xml_response = get_url_or_error(metadata_xml_url)
    xml_response = get_url_or_error(xml_url)

    handeling = create_or_update_handeling_from_raw_metadata_and_content(
        identifier,
        sru_record,
        metadata_xml_response.text,
        html_response.text,
        False,
        xml_response.text,
    )

    return handeling


@shared_task
def crawl_handeling_using_sru_record_task(sru_record_string: str) -> int:
    """Wrapper function to call crawl_handeling_using_sru_record as a celery task"""

    handeling = crawl_handeling_using_sru_record(ET.fromstring(sru_record_string))

    return handeling.pk


def crawl_all_handelingen_within_koop_sru_query(
    query: str, queue_tasks=False
) -> list[Handeling] | list[AsyncResult]:
    """
    Crawl al Handeling items which can be found by the given KOOP SRU query

    Example queries:
        (c.product-area==officielepublicaties AND w.publicatienaam=Handelingen AND dt.date >= 2025-01-01)

    Note that your query MUST ensure that only entries with w.publicatienaam=Handelingen are received.
    """

    results = []
    records = koop_sru_api_request_all(query)

    for record in records:
        try:
            logger.debug("Crawling %s", record)

            if queue_tasks:
                async_handeling = crawl_handeling_using_sru_record_task.delay(
                    ET.tostring(record, encoding="unicode")
                )
                results.append(async_handeling)
            else:
                new_result = crawl_handeling_using_sru_record(record)
                results.append(new_result)
        except CrawlerException:
            logger.error("Failed to crawl Handeling record %s", record)

    return results


def crawl_all_handelingen_in_vergaderjaar(
    vergaderjaar: str, queue_tasks=False
) -> list[Handeling] | list[AsyncResult]:
    """Crawl all publications in the Handelingen with a publicatiedatum within a vergaderjaar, e.g. 2020-2021, 1996-1997"""

    today = datetime.date.today()
    current_year = today.year
    if today.month > 9:
        vergaderjaren = [f"{x}-{x+1}" for x in range(1995, current_year + 1)]
    else:
        vergaderjaren = [f"{x}-{x+1}" for x in range(1995, current_year)]

    if vergaderjaar not in vergaderjaren:
        raise CrawlerException(f"Provided invalid vergaderjaar {vergaderjaar}")

    return crawl_all_handelingen_within_koop_sru_query(
        f"(c.product-area==officielepublicaties AND w.publicatienaam=Handelingen AND w.vergaderjaar={vergaderjaar})",
        queue_tasks=queue_tasks
    )
