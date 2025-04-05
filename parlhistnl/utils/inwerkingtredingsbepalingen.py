"""
    parlhist/parlhistnl/utils/inwerkingtredingsbepalingen.py

    Assorted utilities for experiments

    Copyright 2025 Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging
import re

from enum import Enum
from os import environ

import requests

from rdflib import Graph

from parlhistnl.models import Staatsblad
from parlhistnl.crawler.utils import CrawlerException

logger = logging.getLogger(__name__)
logging.getLogger("rdflib").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

# iwt_re: re.Pattern = re.compile(
#     r"(de\s+artikelen\s+van\s+deze\s+(rijks)?wet\s+treden|deze\s+(rijks)?wet\s+treedt)(,?\s*met\s+uitzondering\s+van[\w,\s]+,\s*)?(,\s+onder\s+toepassing\s+van\s+artikel\s+12,\s+eerste lid,\s+van\s+de\s+Wet\s+raadgevend\s+referendum,)?\s+in\s+werking[\w,:;().–\-\s\\/]+(?=artikel|(?<=.)lasten\s+en\s+bevelen)",
#     re.IGNORECASE,
# )

iwt_re = re.compile(
    r"(de\s+artikelen\s+van\s+deze\s+(rijks)?wet\s+treden|de(ze)?\s+(rijks)?wet(,?\s*met\s+uitzondering\s+van[\w,\s]+,\s*)?\s+treedt|indien\s+het\s+bij\s+(koninklijke\s+boodschap|geleidende\s+brief)\s+van\s+\d{1,2}\s+\w{3,12}\s+\d{4}\s+ingediende\s+voorstel\s+van\s+wet|onder\s+toepassing\s+van\s+[\w\s]+treedt\s+deze\s+wet\s+in\s+werking)[\w,:;().’–\-\s\\/]+(?=deze\s+wet\s+wordt\s+aangehaald\s+als|lasten\s+en\s+bevelen)",
    re.IGNORECASE
)

kb_re: re.Pattern = re.compile(
    r"bij\s+koninklijk\s+besluit\s+te\s+bepalen\s+tijdstip", re.IGNORECASE
)
dif_re: re.Pattern = re.compile(
    r"verschillend\s+kan\s+worden\s+(vast)?gesteld", re.IGNORECASE
)
date_in_title_re: re.Pattern = re.compile(
    r"van\s+\d?\d\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{4}\s+", re.IGNORECASE
)

try:
    LIDO_COOKIES = {
        "JSESSIONID": environ["PARLHIST_LIDO_JSESSIONID"],
        "INGRESSCOOKIE": environ["PARLHIST_LIDO_INGRESSCOOKIE"]
    }
except KeyError:
    logger.warning("Appropriate environment variables are not set; no LiDO authentication cookies set.")
    LIDO_COOKIES = {}

LIDO_GET_LINKS_API_URL = "https://linkeddata.overheid.nl/service/get-links"

# All the Staatsblad.StaatsbladTypes which are a koninklijk besluit and which may contain any delegated
# decisions on the inwerkingtredingsdatum of a wet.
STAATSBLADTYPES_KB = [Staatsblad.StaatsbladType.KKB, Staatsblad.StaatsbladType.AMVB, Staatsblad.StaatsbladType.RIJKSAMVB]


class InwerkingtredingsbepalingType(Enum):
    """Enum class for simple 3-way categorisation of inwerkingtredingsbepalingen"""

    DELEGATIE_EN_DIFFERENTIATIE = (
        "Inwerkingtredingsbepaling met delegatie en differentiatie"
    )
    DELEGATIE_ZONDER_DIFFERENTIATIE = (
        "Inwerkgintredingsbepaling met delegatie zonder differentiatie"
    )
    GEEN_DELEGATIE = "Inwerkingtredingsbepaling zonder delegatie"
    GEEN_INWERKINGTREDINGSBEPALING = "Geen inwerkingtredingsbepaling"
    ONBEKEND = "Onbekend"


def find_inwerkingtredingsbepaling(stb: Staatsblad) -> dict:
    """
    Find inwerkingtredingsbepaling in the given stb

    Returns a dict with:
        cleaned_text (always): the cleaned text of stb that was evaluated
        label (always): a InwerkingtredingsbepalingType value
        start, end, text: if an inwerkingtredingsbepaling was found in the text, the start, end and actual text value of it.
    """

    if stb.is_vaststelling_grond_grondwetswijziging:
        label = InwerkingtredingsbepalingType.GEEN_INWERKINGTREDINGSBEPALING

    cleaned_text_1 = stb.tekst.replace("\xa0", " ")
    cleaned_text = f"{stb.preferred_url}\n{cleaned_text_1}"

    result_dict = {"cleaned_text": cleaned_text}

    matches = list(iwt_re.finditer(cleaned_text))

    labeled_matches = []

    for match in matches:
        matcheskb = list(kb_re.finditer(match.group(0)))
        matchesdif = list(dif_re.finditer(match.group(0)))

        if len(matcheskb) > 0 and len(matchesdif) > 0:
            label = InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        elif len(matcheskb) > 0 and len(matchesdif) == 0:
            label = InwerkingtredingsbepalingType.DELEGATIE_ZONDER_DIFFERENTIATIE
        else:
            label = InwerkingtredingsbepalingType.GEEN_DELEGATIE

        labeled_matches.append(
            {
                "start": match.start(0),
                "end": match.end(0),
                "text": match.group(0),
                "label": label
            }
        )

    logger.debug("Found %s", labeled_matches)

    if len(labeled_matches) > 1:
        logger.info("Found multiple inwerkingtredingsbepalingen for %s", stb)

    if len(labeled_matches) > 0:
        result_dict["start"] = labeled_matches[0]["start"]
        result_dict["end"] = labeled_matches[0]["end"]
        result_dict["text"] = labeled_matches[0]["text"]
        result_dict["label"] = labeled_matches[0]["label"]
    else:
        logger.warning("No inwerkingtredingsbepalingen found")
        result_dict["label"] = InwerkingtredingsbepalingType.ONBEKEND

    result_dict["labeled_matches"] = labeled_matches

    return result_dict


def find_related_inwerkingtredingskb(stb: Staatsblad) -> set[Staatsblad]:
    """
    Given the Staatsblad object for some wet or amvb, try to retrieve all related inwerkingtredingskbs.
    """

    resultset = set()

    if (
        stb.staatsblad_type != Staatsblad.StaatsbladType.WET
        and stb.staatsblad_type != Staatsblad.StaatsbladType.AMVB
        and stb.staatsblad_type != Staatsblad.StaatsbladType.RIJKSWET
        and stb.staatsblad_type != Staatsblad.StaatsbladType.RIJKSAMVB
    ):
        logger.error(
            "Tried to find related inwerkingtredingskb for a stb that is not of type WET, AMVB, RIJKSWET or RIJKSAMVB"
        )
        return resultset

    # Just search for any KKB that contains the reference to our stb in the metadata XML
    # Note thate an AMVB or RIJKSAMVB can also contain the inwerkingtredingsbepaling; see for example
    # article II(2) of Stb. 2014, 405 https://zoek.officielebekendmakingen.nl/stb-2014-405.html
    kkbs_metadata_xml_stb_ref = Staatsblad.objects.filter(
        staatsblad_type__in=STAATSBLADTYPES_KB,
        raw_metadata_xml__icontains=f"Stb. {stb.jaargang}, {stb.nummer}",
        publicatiedatum__gte=stb.publicatiedatum  # Assume that the inwerkingtredingskb is never younger than the stb
    )

    # logger.info(kkbs_metadata_xml_stb_ref)

    resultset.update(kkbs_metadata_xml_stb_ref)

    # See if there is possibly a citeertitel in the metadata
    if "dctermsalternative" in stb.metadata_json:
        citeertitel = stb.metadata_json["dctermsalternative"]
        logger.info("Found citeertitel %s", citeertitel)

        # Since we have found a citeertitel, we can also search for that
        kkbs_metadata_xml_citeertitel = Staatsblad.objects.filter(
            staatsblad_type__in=STAATSBLADTYPES_KB,
            raw_metadata_xml__icontains=citeertitel,
            publicatiedatum__gte=stb.publicatiedatum
        )

        # logger.info(kkbs_metadata_xml_citeertitel)

        resultset.update(kkbs_metadata_xml_citeertitel)
    else:
        # Since there is no citeertitel, lets try to find a KKB that mentions the full title of our stb.
        kkbs_metadata_xml_full_title = Staatsblad.objects.filter(
            staatsblad_type__in=STAATSBLADTYPES_KB,
            raw_metadata_xml__icontains=stb.titel,
            publicatiedatum__gte=stb.publicatiedatum
        )

        resultset.update(kkbs_metadata_xml_full_title)

        # Alternatively, we try to remove the date from the title and search for that
        stb_title_without_date = date_in_title_re.sub("", stb.titel)
        logger.debug("Cleaned title %s to %s", stb.titel, stb_title_without_date)
        kkbs_metadata_xml_full_title_no_date = Staatsblad.objects.filter(
            staatsblad_type__in=STAATSBLADTYPES_KB,
            raw_metadata_xml__icontains=stb_title_without_date,
            publicatiedatum__gte=stb.publicatiedatum
        )

        resultset.update(kkbs_metadata_xml_full_title_no_date)

    # TODO: Search within the text itself if we haven't found anything

    return resultset


def find_inwerkingtredingskb_via_lido(stb: Staatsblad) -> set[Staatsblad]:
    """
    Use the authenticated /get-links API endpoint from LiDO to find all Staatsblad publications which are a 'inwerkingtredingsbron'
    for the given Staatsblad

    Note: this implementation expects that you have defined PARLHIST_LIDO_JSESSIONID and PARLHIST_LIDO_INGRESSCOKIE environment
    variables appropriately to authenticate with the LiDO API.

    For more information on the API, please see https://linkeddata.overheid.nl/front/portal/services
    """

    params = {
        "ext-id": f"OEP:{stb.stbid}"
    }

    try:
        rdfxml_response = requests.get(LIDO_GET_LINKS_API_URL, params=params, cookies=LIDO_COOKIES, timeout=600)
    except requests.exceptions.ReadTimeout as exc:
        logger.fatal("RDF XML request timed out %s", exc)
        raise CrawlerException from exc

    if rdfxml_response.status_code != 200:
        logger.critical("RDF XML request resulted in not-OK status code %s", rdfxml_response)
        raise CrawlerException

    rdfgraph = Graph()

    rdfgraph.parse(rdfxml_response.content, format="xml")

    # First, we find all the subjects that have the given stb-publication as a 'ontstaansbron'
    ontstaan = rdfgraph.query(f"""
                              SELECT *
                              WHERE {{
                                ?sub <http://linkeddata.overheid.nl/terms/refereertAan> ?obj .
                                filter contains(?obj, 'linktype=http://linkeddata.overheid.nl/terms/linktype/id/bwb-ontstaansbron|target=oep|uri=OEP:{stb.stbid}')
                              }}
                              """
                              )

    return ontstaan, rdfgraph
