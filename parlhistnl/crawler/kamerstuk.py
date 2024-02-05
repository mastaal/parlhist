"""
    parlhist/parlhistnl/crawler/kamerstuk.py

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from parlhistnl.models import Kamerstuk, KamerstukDossier
from parlhistnl.crawler.utils import CrawlerException, get_url_or_error

logger = logging.getLogger(__name__)


def __get_dossiertitel(xml: ET.Element) -> str:
    """Get the dossiertitel from a parsed metadata xml"""

    return xml.findall("metadata[@name='OVERHEIDop.dossiertitel']")[0].get("content")


def __get_documentitel(xml: ET.Element) -> str:
    """Get the dossiertitel from a parsed metadata xml"""

    return xml.findall("metadata[@name='OVERHEIDop.documenttitel']")[0].get("content")


def __get_indiener(xml: ET.Element) -> str:
    """Get the dossiertitel from a parsed metadata xml"""

    try:
        return xml.findall("metadata[@name='OVERHEIDop.indiener']")[0].get("content")
    except IndexError:
        return "GEEN_INDIENER_OPGEGEVEN"


def __get_vergaderjaar(xml: ET.Element) -> str:
    """Get the dossiertitel from a parsed metadata xml"""

    return xml.findall("metadata[@name='OVERHEIDop.vergaderjaar']")[0].get("content").replace("-", "")


def __get_kamer(xml: ET.Element) -> str:
    """Get the dossiertitel from a parsed metadata xml"""

    raw = xml.findall("metadata[@scheme='OVERHEID.StatenGeneraal']")[0].get("content")

    if raw == "Tweede Kamer der Staten-Generaal":
        return "tk"
    elif raw == "Eerste Kamer der Staten-Generaal":
        return "ek"
    else:
        logger.error("Can't get kamer in %s, assuming tk", raw)
        # TODO: Assume based on ondernummer
        return "tk"


def __get_kamerstuktype_from_title(title: str, xml: ET.Element) -> str:
    """Guess the kamerstuk document type from the title"""

    logger.debug("Assessing kamerstuktype for title %s", title)

    try:
        opgegeven_kamerstuktype = xml.find("metadata[@scheme='OVERHEIDop.KamerstukTypen']").get("content")
        logger.debug("Opgegeven kamerstuktype: %s", opgegeven_kamerstuktype)
    except AttributeError:
        logger.warning("Geen opgegeven kamerstuktype gevonden voor %s", title)

    if opgegeven_kamerstuktype == "Brief" or opgegeven_kamerstuktype == "Amendement" or opgegeven_kamerstuktype == "Motie":
        return opgegeven_kamerstuktype

    if opgegeven_kamerstuktype == "Voorstel van wet" or opgegeven_kamerstuktype == "Koninklijke boodschap":
        return opgegeven_kamerstuktype

    if opgegeven_kamerstuktype == "Memorie van toelichting" or opgegeven_kamerstuktype == "Jaarverslag":
        return opgegeven_kamerstuktype

    if opgegeven_kamerstuktype == "Verslag":
        return opgegeven_kamerstuktype

    if title.startswith("Motie") or title.startswith("Gewijzigde motie"):
        return Kamerstuk.KamerstukType.MOTIE

    if title.startswith("Amendement") or title.startswith("Gewijzigd amendement"):
        return Kamerstuk.KamerstukType.AMENDEMENT

    if title.startswith("Voorstel van wet") or title.startswith("Gewijzigd voorstel van wet"):
        return Kamerstuk.KamerstukType.WETSVOORSTEL

    if title.startswith("Advies Afdeling advisering Raad van State"):
        return Kamerstuk.KamerstukType.ADVIES_RVS

    if title.startswith("Voorlopig verslag") or title.startswith("Verslag") or title.startswith("Eindverslag") or title.startswith("Nader voorlopig verslag"):
        return Kamerstuk.KamerstukType.VERSLAG

    if title == "Nota naar aanleiding van het verslag":
        return Kamerstuk.KamerstukType.NOTA_NA_VERSLAG

    if title.lower().startswith("memorie van toelichting"):
        return Kamerstuk.KamerstukType.MEMORIE_VAN_TOELICHTING

    if title.lower().startswith("memorie van antwoord") or title.lower().startswith("nadere memorie van antwoord"):
        return Kamerstuk.KamerstukType.MEMORIE_VAN_ANTWOORD

    if title.startswith("Voorlichting van de Afdeling advisering van de Raad van State"):
        return Kamerstuk.KamerstukType.VOORLICHTING_RVS

    if title.lower().startswith("jaarverslag"):
        return Kamerstuk.KamerstukType.JAARVERSLAG

    if "nota van wijziging" in title.lower():
        # Beware, this lax check may result in errors
        return "Nota van wijziging"

    return "Onbekend"


# TODO split this up just like handeling to enable easy re-indexing of existing kamerstukken
def crawl_kamerstuk(dossiernummer: str, ondernummer: str, update=False) -> Kamerstuk:
    """Crawl a kamerstuk"""

    logger.info("Crawling kamerstuk %s, %s", dossiernummer, ondernummer)

    base_url: str = f"https://zoek.officielebekendmakingen.nl/kst-{dossiernummer}-{ondernummer}"
    html_url = f"{base_url}.html"
    meta_url = f"{base_url}/metadata.xml"

    try:
        existing_kst = Kamerstuk.objects.get(hoofddossier__dossiernummer=dossiernummer, ondernummer=ondernummer)
        logger.info("Kamerstuk already exists")
        if not update:
            logger.info("Update set to false, returning existing kamerstuk")
            return existing_kst
    except Kamerstuk.DoesNotExist:
        existing_kst = None

    # First, check if it could actually exist
    try:
        text_response = get_url_or_error(html_url)
    except CrawlerException as exc:
        logger.critical("This kamerstuk seems to not exist")
        raise CrawlerException("This kamerstuk seems to not exist") from exc

    try:
        meta_response = get_url_or_error(meta_url)
    except CrawlerException as exc:
        logger.fatal("This handeling seems to not exist")
        raise CrawlerException("This handeling seems to not exist") from exc

    xml = ET.fromstring(meta_response.text)

    try:
        documenttitel = __get_documentitel(xml)
    except IndexError as exc:
        logger.critical("Could not get documenttitel for %s %s", dossiernummer, ondernummer)
        raise CrawlerException("Failed to get core metadata") from exc
    try:
        dossiertitel = __get_dossiertitel(xml)
    except IndexError as exc:
        logger.critical("Could not get dossiertitel for %s %s", dossiernummer, ondernummer)
        raise CrawlerException("Failed to get core metadata") from exc
    try:
        indiener = __get_indiener(xml)
    except IndexError:
        logger.error("Could not get indiener for %s %s", dossiernummer, ondernummer)
        indiener = "INDIENER_ONBEKEND"

    try:
        kamer = __get_kamer(xml)
    except IndexError as exc:
        logger.critical("Could not get kamer for %s %s", dossiernummer, ondernummer)
        raise CrawlerException("Failed to get core metadata") from exc
    try:
        vergaderjaar = __get_vergaderjaar(xml)
    except IndexError as exc:
        logger.critical("Could not get vergaderjaar for %s %s", dossiernummer, ondernummer)
        raise CrawlerException("Failed to get core metadata") from exc

    try:
        kamerstuktype = __get_kamerstuktype_from_title(documenttitel, xml)
    except IndexError:
        logger.error("Could not succesfully kamerstuktype for %s %s", dossiernummer, ondernummer)

    # TODO add support for multi-dossier kamerstukken
    dossier, created = KamerstukDossier.objects.get_or_create(dossiernummer=dossiernummer)
    if created or update:
        dossier.dossiertitel = dossiertitel
        dossier.save()

    # TODO: Make specific function for extracting this inner html
    soup = BeautifulSoup(text_response.text, "html.parser")

    elems = soup.select("article div#broodtekst.stuk.broodtekst-container")

    if len(elems) > 1:
        logger.info("Got multiple matches where only one was expected %s %s", dossiernummer, ondernummer)

    inner_html = str(elems[0])

    tekst = elems[0].get_text()

    if update and existing_kst is not None:
        existing_kst.hoofddossier = dossier
        existing_kst.vergaderjaar = vergaderjaar
        existing_kst.kamer = kamer
        existing_kst.kamerstuktype = kamerstuktype
        existing_kst.documenttitel = documenttitel
        existing_kst.indiener = indiener
        existing_kst.tekst = tekst
        existing_kst.raw_html = inner_html
        existing_kst.raw_metadata_xml = meta_response.text
        existing_kst.save()
        kst = existing_kst
    else:
        # Note that if update is false and it already exists, this code path is unreachable
        kst = Kamerstuk.objects.create(
            vergaderjaar=vergaderjaar,
            hoofddossier=dossier,
            ondernummer=ondernummer,  # TODO maybe verify?
            kamer=kamer,
            kamerstuktype=kamerstuktype,
            documenttitel=documenttitel,
            indiener=indiener,
            tekst=tekst,
            raw_html=inner_html,
            raw_metadata_xml=meta_response.text
        )

    logger.debug(kst)

    return kst
