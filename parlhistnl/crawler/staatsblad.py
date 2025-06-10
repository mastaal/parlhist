"""
parlhist/parlhistnl/crawler/staatsblad.py

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
SPDX-FileCopyrightText: 2024-2025 Martijn Staal <parlhist [at] martijn-staal.nl>
SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import datetime
import logging
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from celery import shared_task
from celery.result import AsyncResult

from parlhistnl.models import Staatsblad
from parlhistnl.crawler.utils import (
    CrawlerException,
    get_url_or_error,
    koop_sru_api_request_all,
    XML_NAMESPACES,
)

logger = logging.getLogger(__name__)


def __get_publicatiedatum(xml: ET.Element) -> datetime.date:
    """Get the publicatiedatum from from a parsed metadata xml"""

    date_str = xml.findall("metadata[@name='DCTERMS.issued']")[0].get("content")

    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    return date


def __get_ondertekendatum(xml: ET.Element) -> datetime.date:
    """Get the ondertekendatum"""
    date_str = xml.findall("metadata[@name='OVERHEIDop.datumOndertekening']")[0].get(
        "content"
    )

    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    return date


def __get_titel(xml: ET.Element) -> str:
    """Get the titel from a parsed metadata xml"""

    return xml.findall("metadata[@name='DC.title']")[0].get("content")


def __get_staatsblad_type(xml: ET.Element, titel: str) -> Staatsblad.StaatsbladType:
    """Get the StaatsbladType"""

    xml_type = xml.findall(
        "metadata[@name='DC.type'][@scheme='OVERHEIDop.Staatsblad']"
    )[0].get("content")

    if xml_type == "Wet":
        return Staatsblad.StaatsbladType.WET

    if xml_type == "Rijkswet":
        return Staatsblad.StaatsbladType.RIJKSWET

    if xml_type == "AMvB":
        return Staatsblad.StaatsbladType.AMVB

    if xml_type == "RijksAMvB":
        return Staatsblad.StaatsbladType.RIJKSAMVB

    if xml_type == "Verbeterblad":
        return Staatsblad.StaatsbladType.VERBETERBLAD

    # TODO: Further disambiguate between possible KKB's so that direct filtering on inwerkingtreding-KB's is possible
    if xml_type == "Klein Koninklijk Besluit":
        return Staatsblad.StaatsbladType.KKB

    if (
        xml_type == "Beschikking"
        and "plaatsing in het Staatsblad van de tekst" in titel
    ):
        return Staatsblad.StaatsbladType.INTEGRALE_TEKSTPLAATSING

    return Staatsblad.StaatsbladType.ONBEKEND


# TODO split this up just like handeling to enable easy re-indexing of existing Staatsblad publications
def crawl_staatsblad(
    jaargang: int, nummer: str, versienummer="", update=False, preferred_url=None
) -> Staatsblad:
    """Crawl a Staatsblad"""

    logger.info("Crawling Staatsblad %s, %s, %s", jaargang, nummer, versienummer)

    if preferred_url is None:
        if versienummer == "":
            base_url: str = (
                f"https://zoek.officielebekendmakingen.nl/stb-{jaargang}-{nummer}"
            )
        else:
            base_url: str = (
                f"https://zoek.officielebekendmakingen.nl/stb-{jaargang}-{nummer}-{versienummer}"
            )
        html_url = f"{base_url}.html"
        meta_url = f"{base_url}/metadata.xml"
    else:
        html_url: str = preferred_url
        meta_url = html_url.replace(".html", "/metadata.xml")

    xml_url = html_url.replace(".html", ".xml")

    try:
        existing_stb = Staatsblad.objects.get(
            jaargang=jaargang, nummer=nummer, versienummer=versienummer
        )
        logger.info("Staatsblad already exists")
        if not update:
            logger.info("Update set to false, returning existing Staatsblad")
            return existing_stb
    except Staatsblad.DoesNotExist:
        existing_stb = None

    # First, check if it could actually exist
    try:
        text_response = get_url_or_error(html_url)
    except CrawlerException as exc:
        logger.critical(
            "Could not retrieve HTML version for this Staatsblad, tried %s", html_url
        )
        raise CrawlerException(
            "Could not retrieve HTML version for this Staatsblad"
        ) from exc

    try:
        meta_response = get_url_or_error(meta_url)
    except CrawlerException as exc:
        logger.fatal(
            "Could not retrieve XML metadata for this Staatsblad, tried %s", meta_url
        )
        raise CrawlerException(
            "Could not retrieve XML metadata for this Staatsblad"
        ) from exc

    try:
        xml_response = get_url_or_error(xml_url)
    except CrawlerException as exc:
        logger.fatal(
            "Could not retrieve XML metadata for this Staatsblad, tried %s", xml_url
        )
        raise CrawlerException(
            "Could not retrieve XML metadata for this Staatsblad"
        ) from exc

    metadata_xml = ET.fromstring(meta_response.text)

    try:
        publicatiedatum = __get_publicatiedatum(metadata_xml)
    except IndexError:
        logger.error(
            "Could not get publicatiedatum for %s %s (%s), using fallback date 1800-01-01",
            jaargang,
            nummer,
            meta_url,
        )
        publicatiedatum = datetime.date(1800, 1, 1)

    try:
        ondertekendatum = __get_ondertekendatum(metadata_xml)
    except IndexError:
        logger.error(
            "Could not get ondertekendatum for %s %s (%s), using fallback date 1800-01-01",
            jaargang,
            nummer,
            meta_url,
        )
        ondertekendatum = datetime.date(1800, 1, 1)

    try:
        titel = __get_titel(metadata_xml)
    except IndexError as exc:
        logger.critical(
            "Could not get titel for %s %s (%s)", jaargang, nummer, meta_url
        )
        raise CrawlerException("Failed to get core metadata") from exc

    try:
        staatsblad_type = __get_staatsblad_type(metadata_xml, titel)
    except IndexError:
        logger.error(
            "Could not successfully detect StaatsbladType for %s %s", jaargang, nummer
        )
        staatsblad_type = Staatsblad.StaatsbladType.ONBEKEND

    # Actually parse the behandelde_dossiers (OVERHEIDop.behandeldDossier)

    # Also store the metadata in JSON
    metadata_json = {}
    for metadata in metadata_xml.findall("metadata"):
        metadata_json[metadata.get("name").replace(".", "").lower()] = metadata.get(
            "content"
        )

    # TODO: Make specific function for extracting this inner html
    soup = BeautifulSoup(text_response.text, "html.parser")

    inner_text_elements = soup.select(
        "article div#broodtekst.stuk.broodtekst-container"
    )

    if len(inner_text_elements) > 1:
        logger.warning(
            "While extracting the inner html text, multiple matches were found where only one was expected %s",
            html_url,
        )

    inner_html = str(inner_text_elements[0])

    tekst = inner_text_elements[0].get_text()

    if update and existing_stb is not None:
        existing_stb.jaargang = jaargang
        existing_stb.versienummer = versienummer
        existing_stb.titel = titel
        existing_stb.publicatiedatum = publicatiedatum
        existing_stb.ondertekendatum = ondertekendatum
        existing_stb.tekst = tekst
        existing_stb.raw_html = inner_html
        existing_stb.raw_xml = xml_response.text
        existing_stb.raw_metadata_xml = meta_response.text
        existing_stb.metadata_json = metadata_json
        existing_stb.staatsblad_type = staatsblad_type
        existing_stb.preferred_url = preferred_url
        existing_stb.save()
        stb = existing_stb
    else:
        # Note that if update is false and it already exists, this code path is unreachable
        stb = Staatsblad.objects.create(
            jaargang=jaargang,
            nummer=nummer,
            versienummer=versienummer,
            titel=titel,
            tekst=tekst,
            raw_html=inner_html,
            raw_xml=xml_response.text,
            raw_metadata_xml=meta_response.text,
            metadata_json=metadata_json,
            publicatiedatum=publicatiedatum,
            ondertekendatum=ondertekendatum,
            staatsblad_type=staatsblad_type,
            preferred_url=preferred_url,
        )

    logger.debug(stb)

    return stb


@shared_task
def crawl_staatsblad_task(
    jaargang: int, nummer: str, versienummer="", update=False, preferred_url=None
) -> int:
    """Wrapper function for crawl_staatsblad as a celery tasks that returns just the id of the staatsblad in the database"""
    stb = crawl_staatsblad(
        jaargang,
        nummer,
        versienummer=versienummer,
        update=update,
        preferred_url=preferred_url,
    )
    return stb.id


def crawl_all_staatsblad_publicaties_within_koop_sru_query(
    query: str, update=False, queue_tasks=False
) -> list[Staatsblad] | list[AsyncResult]:
    """
    Crawl all Staatsbladen which can be found by the given KOOP SRU query

    Example queries:
        (w.publicatienaam=Staatsblad AND dt.type=Wet AND dt.date >= 2024-06-01)
        (w.publicatienaam=Staatsblad AND dt.type=Wet AND dt.date >= 2024-01-01 AND dt.date <= 2024-12-31)

    Note: Only tested for dt.type=Wet queries.
    """

    results: list[Staatsblad] | list[AsyncResult] = []
    records = koop_sru_api_request_all(query)

    for record in records:
        try:
            logger.debug("Crawling %s", record)
            jaargang_record_xml = record.find(
                ".//overheidwetgeving:jaargang", XML_NAMESPACES
            )
            if jaargang_record_xml is None:
                raise CrawlerException(f"Could not find jaargang record in {record}")
            jaargang_record = jaargang_record_xml.text
            if jaargang_record is None or jaargang_record == "":
                raise CrawlerException(f"Jaargang record has no text in {record}")

            try:
                jaargang_record = int(jaargang_record)
            except ValueError as exc:
                raise CrawlerException(
                    f"Jaargang record could not be converted to int {jaargang_record}, {record}"
                ) from exc

            nummer_record_xml = record.find(
                ".//overheidwetgeving:publicatienummer", XML_NAMESPACES
            )
            if nummer_record_xml is None:
                raise CrawlerException(f"Could not find nummer record in {record}")
            nummer_record = nummer_record_xml.text
            if nummer_record is None or nummer_record == "":
                raise CrawlerException(f"Nummer record has no text in {record}")

            versienummer_xml = record.find(
                ".//overheidwetgeving:versienummer", XML_NAMESPACES
            )
            if versienummer_xml is not None:
                logger.debug("Found versienummer, expecting verbeterblad...")
                versienummer = versienummer_xml.text
            else:
                versienummer = ""

            logger.debug("Found jaargang %s, nummer %s", jaargang_record, nummer_record)

            try:
                preferred_url = record.find(".//gzd:preferredUrl", XML_NAMESPACES).text
                logger.debug("Found preferred url %s", preferred_url)
            except AttributeError:
                logger.warning(
                    "Couldn't find a preferred url for %s %s %s, falling back to default",
                    jaargang_record,
                    nummer_record,
                    record,
                )
                preferred_url = None

            if queue_tasks:
                async_stb = crawl_staatsblad_task.delay(
                    jaargang_record,
                    nummer_record,
                    versienummer=versienummer,
                    update=update,
                    preferred_url=preferred_url,
                )
                results.append(async_stb)
            else:
                stb = crawl_staatsblad(
                    jaargang_record,
                    nummer_record,
                    versienummer=versienummer,
                    update=update,
                    preferred_url=preferred_url,
                )
                results.append(stb)
        except CrawlerException:
            logger.error("Failed to crawl stb-%s-%s", jaargang_record, nummer_record)
        except Exception as exc:
            logger.error(
                "Got an unexpected exception %s in crawling stb %s %s",
                exc,
                jaargang_record,
                nummer_record,
            )

    return results


def crawl_all_staatsblad_publicaties_in_year(
    year: int, update=False, queue_tasks=False
) -> list[Staatsblad] | list[AsyncResult]:
    """
    Crawl all the Staatsblad publicaties with their publicatiedatum within the range of year-01-01 and year-12-31 (inclusive).

    year: any value between 1995 and the current year (inclusive)
    """
    current_year = datetime.date.today().year
    if year not in range(1995, current_year + 1):
        raise CrawlerException("Received invalid year %s", year)

    return crawl_all_staatsblad_publicaties_within_koop_sru_query(
        f"(w.publicatienaam=Staatsblad AND dt.date >= {year}-01-01 AND dt.date <= {year}-12-31)",
        update=update,
        queue_tasks=queue_tasks,
    )
