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

from parlhistnl.models import Staatsblad

logger = logging.getLogger(__name__)
iwt_re: re.Pattern = re.compile(
    r"(de\s+artikelen\s+van\s+deze\s+(rijks)?wet\s+treden|deze\s+(rijks)?wet\s+treedt)(,\s+met\s+uitzondering\s+van[\w,\s]+,\s*)?(,\s+onder\s+toepassing\s+van\s+artikel\s+12,\s+eerste lid,\s+van\s+de\s+Wet\s+raadgevend\s+referendum,)?\s+in\s+werking[\w,\s]+.(\s*indien[\w,\s]+.)?",
    re.IGNORECASE,
)

kb_re: re.Pattern = re.compile(
    r"bij\s+koninklijk\s+besluit\s+te\s+bepalen\s+tijdstip", re.IGNORECASE
)
dif_re: re.Pattern = re.compile(
    r"verschillend\s+kan\s+worden\s+(vast)?gesteld", re.IGNORECASE
)


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

    if len(matches) == 1:
        m = matches[0]

        # find if it contains KB
        matcheskb = list(kb_re.finditer(m.group(0)))

        matchesdif = list(dif_re.finditer(m.group(0)))

        if len(matcheskb) > 0 and len(matchesdif) > 0:
            label = InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        elif len(matcheskb) > 0 and len(matchesdif) == 0:
            label = InwerkingtredingsbepalingType.DELEGATIE_ZONDER_DIFFERENTIATIE
        else:
            label = InwerkingtredingsbepalingType.GEEN_DELEGATIE

        result_dict["start"] = m.start(0)
        result_dict["end"] = m.end(0)
        result_dict["text"] = m.group(0)
    else:
        logger.debug(
            "Multiple matches for inwerkingtredingsbepaling in %s, defaulting to onbekend",
            stb,
        )
        label = InwerkingtredingsbepalingType.ONBEKEND

    result_dict["label"] = label

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
    kkbs_metadata_xml_stb_ref = Staatsblad.objects.filter(
        staatsblad_type=Staatsblad.StaatsbladType.KKB,
        raw_metadata_xml__icontains=f"Stb. {stb.jaargang}, {stb.nummer}",
    )

    logger.info(kkbs_metadata_xml_stb_ref)

    resultset.update(kkbs_metadata_xml_stb_ref)

    # See if there is possibly a citeertitel in the metadata
    if "dctermsalternative" in stb.metadata_json:
        citeertitel = stb.metadata_json["dctermsalternative"]
        logger.info("Found citeertitel %s", citeertitel)
    else:
        citeertitel = None

    if citeertitel is not None:
        # Since we have found a citeertitel, we can also search for that
        kkbs_metadata_xml_citeertitel = Staatsblad.objects.filter(
            staatsblad_type=Staatsblad.StaatsbladType.KKB,
            raw_metadata_xml__icontains=citeertitel,
        )

        logger.info(kkbs_metadata_xml_citeertitel)

        resultset.update(kkbs_metadata_xml_citeertitel)

    return resultset
