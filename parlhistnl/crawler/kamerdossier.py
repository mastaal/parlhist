"""
    parlhist/parlhistnl/crawler/kamerdossier.py

    Copyright 2023, 2024 Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging
import xml.etree.ElementTree as ET

from parlhistnl.models import Kamerstuk
from parlhistnl.crawler.utils import CrawlerException, get_url_or_error
from parlhistnl.crawler.kamerstuk import crawl_kamerstuk

logger = logging.getLogger(__name__)


def get_kamerstukken_in_kamerstukdossier(dossiernummer: str) -> list[tuple[str, str]]:
    """Using the SRU api, get all kamerstukken in a kamerstukdossier

    Returns strings in the same formatting as denoted in other metadata, e.g. '35899;7', '35925-VII;31' or '35979;F'
    """

    # overheid SRU documentation:
    # https://data.overheid.nl/sites/default/files/dataset/d0cca537-44ea-48cf-9880-fa21e1a7058f/resources/Handleiding%2BSRU%2B2.0.pdf
    base_query = f"https://repository.overheid.nl/sru?query=(c.product-area==officielepublicaties AND w.dossiernummer=={dossiernummer})&maximumRecords=1000&startRecord=1"

    try:
        query_response = get_url_or_error(base_query)
    except CrawlerException as exc:
        logger.error("Received exception %s when trying to query the kamerstukken in dossier %s", exc, dossiernummer)
        raise CrawlerException(f"Received exception when trying to query the kamerstukken in dossier {dossiernummer}") from exc

    xml: ET.Element = ET.fromstring(query_response.text)

    number_of_records = int(xml.find("{http://docs.oasis-open.org/ns/search-ws/sruResponse}numberOfRecords").text)

    if number_of_records > 1000:
        logger.critical("More than 1000 results in a kamerdossier!")
        # TODO, implement this case

    records_xml: list[ET.Element] = xml.find("{http://docs.oasis-open.org/ns/search-ws/sruResponse}records").findall("{http://docs.oasis-open.org/ns/search-ws/sruResponse}record")

    kamerstukken: list[str] = []

    for record_xml in records_xml:
        identifier = record_xml.find(".//{http://purl.org/dc/terms/}identifier").text

        if identifier.startswith("kst-"):
            try:
                # TODO This gives problems in kamerstukdossiers with a -, such as the EU Council-related ones
                # It also breaks for budgetary dossiers (e.g. 11111-XVI), and Rijkswetten
                # Seems to be working now?
                if identifier[-2] == "n":
                    # this is a herdruk of an existing kamerstuk!
                    dossiernummer: str = '-'.join(identifier[4:-3].split('-')[:-1])
                    ondernummer: str = '-'.join(identifier[4:].split('-')[-2:])
                else:
                    dossiernummer: str = '-'.join(identifier[4:].split('-')[:-1])
                    ondernummer: str = identifier[4:].split('-')[-1]
                logger.debug("From identifier %s, assumed dossiernummer %s, ondernummer %s", identifier, dossiernummer, ondernummer)
                kamerstukken.append((dossiernummer, ondernummer))
            except Exception as exc:
                logger.info("Couldn't convert %s to kst string, %s", identifier, exc)
        else:
            logger.debug("Found non-kamerstuk record %s", identifier)

    return kamerstukken


def crawl_kamerstukdossier(dossiernummer: str, update=False, ignore_failure=False) -> list[Kamerstuk]:
    """Crawl all kamerstukken in a kamerstukdossier"""

    logger.info("Crawling kamerstukdossier %s", dossiernummer)

    str_kamerstukken = get_kamerstukken_in_kamerstukdossier(dossiernummer)

    kamerstukken: list[Kamerstuk] = []

    for kamerstuk_string in str_kamerstukken:
        logger.info("Crawling %s", kamerstuk_string)
        try:
            kamerstukken.append(crawl_kamerstuk(kamerstuk_string[0], kamerstuk_string[1], update=update))
        except Exception as exc:
            if ignore_failure:
                logger.error("Received error while trying to crawl %s (%s)", kamerstuk_string, exc)
            else:
                raise CrawlerException from exc

    return kamerstukken
