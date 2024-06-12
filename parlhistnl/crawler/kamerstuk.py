"""
    parlhist/parlhistnl/crawler/kamerstuk.py

    Copyright 2023, 2024, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import datetime
import logging
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from parlhistnl.models import Kamerstuk, KamerstukDossier
from parlhistnl.crawler.utils import CrawlerException, get_url_or_error, koop_sru_api_request_all, XML_NAMESPACES

logger = logging.getLogger(__name__)


def __get_documentdatum(xml: ET.Element) -> datetime.date:
    """Get the documentdatum from from a parsed metadata xml"""

    date_str = xml.findall("metadata[@name='DCTERMS.issued']")[0].get("content")

    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    return date


def __get_dossiertitel(xml: ET.Element) -> str:
    """Get the dossiertitel from a parsed metadata xml"""

    return xml.findall("metadata[@name='OVERHEIDop.dossiertitel']")[0].get("content")


def __get_documentitel(xml: ET.Element) -> str:
    """Get the dossiertitel from a parsed metadata xml"""

    try:
        return xml.findall("metadata[@name='OVERHEIDop.documenttitel']")[0].get("content")
    except IndexError:
        # Older metadata format (before 2010-01-01)
        # No separate documenttitel is available, so we must extract it from DC.title.
        # This requires some ugly code, because the titles can be in the form of:
        # "Voorstel van wet van de leden Ten Hoopen, Slob en Van der Burg tot wijziging van het
        # Wetboek van Strafrecht, de Leegstandwet, en enige andere wetten in verband met het verder
        # terugdringen van kraken en leegstand (Wet kraken en leegstand); Amendement; Amendement Jansen
        # ter vervanging van nr. 12 over het koppelen van de strafbaarstelling aan het voldaan hebben
        # aan de meldingsplicht en het aanbod tot ingebruikname"
        dctitle = xml.findall("metadata[@name='DC.title']")[0].get("content")

        return "; ".join(dctitle.split("; ")[1:])


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


def __get_kamerstuktype_from_title(title: str, record: ET.Element, is_tail=False) -> str:
    """Guess the kamerstuk document type from the title"""

    title = title.lower()
    title = title.replace('0', 'o')
    title = title.strip()

    title_split = title.split('; ')
    try:
        title_tail = title_split[1]
    except IndexError:
        title_tail = ""

    try:
        opgegeven_kamerstuktype = record.find(".//overheidwetgeving:subrubriek[@scheme='OVERHEIDop.KamerstukTypen']", XML_NAMESPACES).text
    except AttributeError:
        opgegeven_kamerstuktype = ""

    if (opgegeven_kamerstuktype == "Brief" or
            title.startswith("brief")):
        return Kamerstuk.KamerstukType.BRIEF

    if opgegeven_kamerstuktype == "Amendement":
        return Kamerstuk.KamerstukType.AMENDEMENT

    if opgegeven_kamerstuktype == "Motie":
        return Kamerstuk.KamerstukType.MOTIE

    if opgegeven_kamerstuktype == "Voorstel van wet":
        return Kamerstuk.KamerstukType.WETSVOORSTEL

    if (opgegeven_kamerstuktype == "Koninklijke boodschap" or
            title.startswith("koninklijke boodschap")):
        return Kamerstuk.KamerstukType.KONINKLIJKE_BOODSCHAP

    if opgegeven_kamerstuktype == "Memorie van toelichting":
        return Kamerstuk.KamerstukType.MEMORIE_VAN_TOELICHTING

    if opgegeven_kamerstuktype == "Jaarverslag":
        return Kamerstuk.KamerstukType.JAARVERSLAG

    if opgegeven_kamerstuktype == "Verslag":
        return Kamerstuk.KamerstukType.VERSLAG

    if title.startswith("motie") or title.startswith("gewijzigde motie"):
        return Kamerstuk.KamerstukType.MOTIE

    if title.startswith("amendement") or title.startswith("gewijzigd amendement") or title.startswith("nader gewijzigd amendement"):
        return Kamerstuk.KamerstukType.AMENDEMENT

    if (title.startswith("voorstel van wet") or
            title.startswith("gewijzigd voorstel van wet") or
            title.startswith("ontwerp van wet")):
        return Kamerstuk.KamerstukType.WETSVOORSTEL

    if title.endswith("voorstel van wet") or title.endswith("gewijzigd voorstel van wet"):
        return Kamerstuk.KamerstukType.WETSVOORSTEL

    if title.startswith("advies afdeling advisering raad van state") or title.startswith("advies raad van state"):
        return Kamerstuk.KamerstukType.ADVIES_RVS

    if title.startswith("voorlopig verslag") or title.startswith("verslag") or title.startswith("eindverslag") or title.startswith("nader voorlopig verslag"):
        return Kamerstuk.KamerstukType.VERSLAG

    if title.endswith("voorlopig verslag") or title.endswith("verslag") or title.endswith("eindverslag") or title.startswith("nader voorlopig verslag"):
        return Kamerstuk.KamerstukType.VERSLAG

    if title.startswith("nota naar aanleiding van het") or title.endswith("nota naar aanleiding van het"):
        return Kamerstuk.KamerstukType.NOTA_NA_VERSLAG

    if title.startswith("memorie van toelichting"):
        return Kamerstuk.KamerstukType.MEMORIE_VAN_TOELICHTING

    if title.endswith("memorie van toelichting"):
        return Kamerstuk.KamerstukType.MEMORIE_VAN_TOELICHTING

    if title.startswith("memorie van antwoord") or title.startswith("nadere memorie van antwoord"):
        return Kamerstuk.KamerstukType.MEMORIE_VAN_ANTWOORD

    if title.endswith("memorie van antwoord") or title.endswith("nadere memorie van antwoord"):
        return Kamerstuk.KamerstukType.MEMORIE_VAN_ANTWOORD

    if title.startswith("voorlichting van de afdeling advisering van de raad van state"):
        return Kamerstuk.KamerstukType.VOORLICHTING_RVS

    if title.lower().startswith("jaarverslag"):
        return Kamerstuk.KamerstukType.JAARVERSLAG

    if "nota van wijziging" in title.lower():
        # Beware, this lax check may result in errors
        return Kamerstuk.KamerstukType.NOTA_VAN_WIJZIGING

    print(f"Can't determine KamerstukType for {title}, trying to run on the tail")

    if not is_tail:
        tail_type = __get_kamerstuktype_from_title(title_tail, record, is_tail=True)

        print(f"Found type {tail_type} using tail {title_tail}")
        return tail_type

    return Kamerstuk.KamerstukType.ONBEKEND


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
        documentdatum = __get_documentdatum(xml)
    except IndexError as exc:
        logger.error("Could not get documentdatum for %s %s, using fallback date 1800-01-01", dossiernummer, ondernummer)
        documentdatum = datetime.date(1800, 1, 1)
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
        existing_kst.documentdatum = documentdatum
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
            raw_metadata_xml=meta_response.text,
            documentdatum=documentdatum
        )

    logger.debug(kst)

    return kst


def crawl_all_kamerstukken_within_koop_sru_query(query: str, update=False) -> list[Kamerstuk]:
    """"Crawl all Kamerstukken which can be found by the given KOOP SRU query"""

    results: list[Kamerstuk] = []
    records = koop_sru_api_request_all(query)

    for record in records:
        try:
            logger.debug("Crawling %s", record)
            dossiernummer_record = record.find(".//overheidwetgeving:dossiernummer", XML_NAMESPACES).text
            ondernummer_record = record.find(".//overheidwetgeving:ondernummer", XML_NAMESPACES).text

            kst = crawl_kamerstuk(dossiernummer_record, ondernummer_record, update=update)
            results.append(kst)
        except CrawlerException:
            logger.error("Failed to crawl kst-%s-%s", dossiernummer_record, ondernummer_record)

    return results
