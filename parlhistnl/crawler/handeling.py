"""
    parlhist/parlhistnl/crawler/handeling.py

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from django.db.models import QuerySet

from parlhistnl.models import Handeling, Vergadering, Kamerstuk, KamerstukDossier

from parlhistnl.crawler.utils import CrawlerException, get_url_or_error
from parlhistnl.crawler.kamerstuk import crawl_kamerstuk
from parlhistnl.crawler.kamerdossier import crawl_kamerstukdossier

logger = logging.getLogger(__name__)


def __get_titel(xml: ET.Element) -> str:
    """Get the titel from a parsed metadata xml"""

    return xml.findall("metadata[@name='DC.title']")[0].get("content")


def __get_handeling_type(xml: ET.Element) -> str:
    """Get the handelingen type from a parsed metadata xml"""

    return xml.findall(
        "metadata[@name='DC.type'][@scheme='OVERHEIDop.HandelingTypen']"
    )[0].get("content")


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


def crawl_vergadering_subitem(
    vergadering: Vergadering, item: int, recrawl=False
) -> Handeling:
    """Crawl a Handeling subitem of a vergadering"""

    try:
        existing_handeling = Handeling.objects.get(
            vergadering=vergadering, ondernummer=item
        )
    except Handeling.DoesNotExist:
        existing_handeling = None

    if recrawl or existing_handeling is None:
        logger.info("Crawling new handeling %s %s", vergadering, item)
        base_url = f"https://zoek.officielebekendmakingen.nl/h-{vergadering.kamer}-{vergadering.vergaderjaar}-{vergadering.nummer}-{item}"
        html_url = f"{base_url}.html"
        meta_url = f"{base_url}/metadata.xml"

        try:
            text_response = get_url_or_error(html_url)
            meta_response = get_url_or_error(meta_url)
        except CrawlerException as exc:
            logger.error(
                "Couldn't crawl %s, assuming this vergadering subitem does not exist",
                html_url,
            )
            raise CrawlerException(
                "This vergadering subitem seems to not exist"
            ) from exc

        return create_or_update_handeling_from_raw_metadata_and_content(
            vergadering, item, meta_response.text, text_response.text, False
        )
    else:
        logger.info(
            "Not recrawling existing handeling %s; updating metadata based on saved information",
            existing_handeling,
        )
        return create_or_update_handeling_from_raw_metadata_and_content(
            vergadering,
            item,
            existing_handeling.raw_metadata_xml,
            existing_handeling.raw_html,
            True,
        )


def create_or_update_handeling_from_raw_metadata_and_content(
    vergadering: Vergadering,
    item: int,
    raw_metadata_xml: str,
    raw_html: str,
    raw_html_is_inner_html: bool,
) -> Handeling:
    """Create or update a Handeling from the raw metadata and raw html, either from new requests or from stored raw data

    Always updates if an existing Handeling.
    """
    xml = ET.fromstring(raw_metadata_xml)
    titel = __get_titel(xml)
    handelingtype = __get_handeling_type(xml)
    uncrawled = __get_behandelde_kamerstukdossiers_and_kamerstukken(xml)

    data = {"uncrawled": uncrawled}
    logger.debug(data)

    soup = BeautifulSoup(raw_html, "html.parser")
    if not raw_html_is_inner_html:
        elems = soup.select("article div#broodtekst.stuk.broodtekst-container")

        if len(elems) > 1:
            logger.info(
                "Got multiple matches where only one was expected %s %s",
                vergadering,
                item,
            )

        inner_html = str(elems[0])

        tekst = elems[0].get_text()
    else:
        tekst = soup.get_text()
        inner_html = raw_html

    logger.debug(vergadering)
    logger.debug(item)
    logger.debug(titel)
    logger.debug(handelingtype)

    handeling, _ = Handeling.objects.get_or_create(
        vergadering=vergadering,
        ondernummer=item,
    )

    handeling.titel = titel
    handeling.handelingtype = handelingtype
    handeling.tekst = tekst
    handeling.raw_html = inner_html
    handeling.raw_metadata_xml = raw_metadata_xml
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
