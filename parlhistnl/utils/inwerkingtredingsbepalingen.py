"""
    parlhist/parlhistnl/utils/inwerkingtredingsbepalingen.py

    Assorted utilities for experiments

    Copyright 2025 Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import datetime
import logging
import re

from enum import Enum
from os import environ

import requests

from rdflib import Graph, URIRef

from parlhistnl.models import Staatsblad
from parlhistnl.crawler.utils import CrawlerException

logger = logging.getLogger(__name__)
logging.getLogger("rdflib").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

iwt_re = re.compile(
    r"(de\s+artikelen\s+van\s+deze\s+(rijks)?wet\s+treden|de(ze)?\s+(rijks)?wet(,?\s*met\s+uitzondering\s+van[\w,\s]+,\s*)?\s+(treedt|treden)|indien\s+het\s+bij\s+(koninklijke\s+boodschap|geleidende\s+brief)\s+van\s+\d{1,2}\s+\w{3,12}\s+\d{4}\s+ingediende\s+voorstel\s+van\s+wet\s+in\s+werking\s+treedt\s+,\s+treedt\s+deze\s+wet|onder\s+toepassing\s+van\s+[\w\s]+treedt\s+deze\s+wet\s+in\s+werking)",
    re.IGNORECASE
)

kb_re: re.Pattern = re.compile(
    r"bij\s+koninklijk\s+besluit\s+(te\s+bepalen|vast\s+te\s+stellen)\s+tijdstip", re.IGNORECASE
)
dif_re: re.Pattern = re.compile(
    r"verschillend\s+kan\s+worden\s+((vast)?gesteld|bepaald)", re.IGNORECASE
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

    cleaned_text_1 = stb.tekst.replace("\xa0", " ")
    cleaned_text = f"{stb.preferred_url}\n{cleaned_text_1}"

    result_dict = {"cleaned_text": cleaned_text}
    labeled_matches = []

    artikelen = stb.get_articles_list()
    inwerkingtredingsartikelen = []

    for artikel in artikelen:
        if iwt_re.search(artikel) is not None:
            inwerkingtredingsartikelen.append(artikel)

    logger.debug("Found %s inwerkingtredingsbepalingen", len(inwerkingtredingsartikelen))

    for inwerkingtredingsartikel in inwerkingtredingsartikelen:
        matcheskb = list(kb_re.finditer(inwerkingtredingsartikel))
        matchesdif = list(dif_re.finditer(inwerkingtredingsartikel))

        if len(matcheskb) > 0 and len(matchesdif) > 0:
            label = InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        elif len(matcheskb) > 0 and len(matchesdif) == 0:
            label = InwerkingtredingsbepalingType.DELEGATIE_ZONDER_DIFFERENTIATIE
        else:
            label = InwerkingtredingsbepalingType.GEEN_DELEGATIE

        # Look up the inwerkingtredingsartikel in the base text
        cleaned_inwerkingtredingsartikel = inwerkingtredingsartikel.replace("\xa0", " ")

        if cleaned_inwerkingtredingsartikel in cleaned_text:
            start = cleaned_text.find(cleaned_inwerkingtredingsartikel)
            end = start + len(cleaned_inwerkingtredingsartikel)

            labeled_matches.append(
                {
                    "start": start,
                    "end": end,
                    "text": cleaned_inwerkingtredingsartikel,
                    "label": label
                }
            )
        else:
            logger.critical("Could not look up the inwerkingtredingsbepaling in the original text")

    logger.debug("Found %s in %s", labeled_matches, stb.stbid)

    if len(labeled_matches) > 0:
        result_dict["start"] = labeled_matches[0]["start"]
        result_dict["end"] = labeled_matches[0]["end"]
        result_dict["text"] = labeled_matches[0]["text"]
        result_dict["label"] = labeled_matches[0]["label"]
    elif stb.is_vaststelling_grond_grondwetswijziging:
        result_dict["label"] = InwerkingtredingsbepalingType.GEEN_INWERKINGTREDINGSBEPALING
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
    # TODO possibly this query can be rewritten to only get artikelen in the first place
    ontstaan = rdfgraph.query(f"""
                              SELECT *
                              WHERE {{
                                ?sub <http://linkeddata.overheid.nl/terms/refereertAan> ?obj .
                                filter contains(?obj, 'linktype=http://linkeddata.overheid.nl/terms/linktype/id/bwb-ontstaansbron|target=oep|uri=OEP:{stb.stbid}')
                              }}
                              """
                              )

    # We want to get inwerkingtredingsinformation on article-basis, so we need to find all articles
    # in ontstaan that have match ?sub <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://linkeddata.overheid.nl/terms/Artikel>
    ontstaan_artikelen = []

    rdf_type_predicate = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    artikel_type = URIRef("http://linkeddata.overheid.nl/terms/Artikel")
    for result in ontstaan:
        subj = result.sub
        subject_type = rdfgraph.value(subject=subj, predicate=rdf_type_predicate, object=None)

        if subject_type == artikel_type:
            logger.debug("%s if of type artikel, adding", subj)
            ontstaan_artikelen.append(subj)
        else:
            logger.debug("%s has type %s, not artikel", subj, subject_type)
        # TODO error handle if value is none

    artikelen_inwerkingtredingsinformatie = {}
    # Now that we have all the articles that were created in this stb publication, we can search for
    # when these articles entered into force
    for artikel in ontstaan_artikelen:
        inwerkingtredingsbron_query_result = rdfgraph.query(f"""
                                               SELECT ?obj
                                               WHERE {{
                                                    {artikel.n3()} <http://linkeddata.overheid.nl/terms/refereertAan> ?obj .
                                                    filter contains(?obj, 'bwb-inwerkingtredingsbron')
                                               }}
                                               """)

        # The objects for this predicate are all of type string (http://www.w3.org/2001/XMLSchema#string)
        # but have the following structure:
        # 'linktype=http://linkeddata.overheid.nl/terms/linktype/id/bwb-inwerkingtredingsbron|target=oep|uri=OEP:stb-2024-197'
        # We're interested here in the OEP uri.

        inwerkingtredingsbronnen = list(inwerkingtredingsbron_query_result)

        # Try to find the inwerkingtredingsdatum
        inwerkingtredingsdatum_obj = rdfgraph.value(subject=artikel, predicate=URIRef("http://linkeddata.overheid.nl/terms/heeftInwerkingtredingsdatum"), object=None)
        if inwerkingtredingsdatum_obj is not None:
            inwerkingtredingsdatum: datetime.date = inwerkingtredingsdatum_obj.value
        else:
            # We use January 1st 1800 as a marker for 'no inwerkingtredingsdatum found'
            logger.warning("No inwerkingtredingsdatum found for %s", artikel)
            inwerkingtredingsdatum = datetime.date(1800, 1, 1)

        artikelen_inwerkingtredingsinformatie[artikel] = {"inwerkingtredingsdatum": inwerkingtredingsdatum.strftime("%Y-%m-%d"), "inwerkingtredingsbronnen": []}
        if len(inwerkingtredingsbronnen) == 0:
            logger.warning("Could not find any inwerkingtredingsbronnen for %s", artikel)
        else:
            for inwerkingtredingsbron_triple in inwerkingtredingsbronnen:
                inwerkingtredingsbron = inwerkingtredingsbron_triple.obj
                inwerkingtredingsbron_list = inwerkingtredingsbron.value.split('|')
                for item in inwerkingtredingsbron_list:
                    if item.startswith('uri=OEP:'):
                        # This item is the form of: uri=OEP:stb-2024-197
                        inwerkingtredingsbron_stbid = item.split(':')[1]
                        logger.debug("Identified %s as inwerkingtredingsbron for %s", inwerkingtredingsbron_stbid, artikel)
                        _, jaargang_str, nummer_str = inwerkingtredingsbron_stbid.split('-')
                        artikelen_inwerkingtredingsinformatie[artikel]["inwerkingtredingsbronnen"].append({"jaargang": int(jaargang_str), "nummer": int(nummer_str)})

    return artikelen_inwerkingtredingsinformatie, rdfgraph
