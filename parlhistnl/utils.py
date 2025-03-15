"""
    parlhist/parlhistnl/utils.py

    Assorted utilities for experiments

    Copyright 2025 Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging

from parlhistnl.models import Staatsblad

logger = logging.getLogger(__name__)


def find_related_inwerkingtredingskb(stb: Staatsblad) -> list[Staatsblad]:
    """
    Given the Staatsblad object for some wet or amvb, try to retrieve all related inwerkingtredingskbs.
    """

    if (
        stb.staatsblad_type != Staatsblad.StaatsbladType.WET
        and stb.staatsblad_type != Staatsblad.StaatsbladType.AMVB
        and stb.staatsblad_type != Staatsblad.StaatsbladType.RIJKSWET
        and stb.staatsblad_type != Staatsblad.StaatsbladType.RIJKSAMVB
    ):
        logger.error(
            "Tried to find related inwerkingtredingskb for a stb that is not of type WET, AMVB, RIJKSWET or RIJKSAMVB"
        )
        return []

    # Just search for any KKB that contains the reference to our stb in the metadata XML
    kkbs_metadata_xml_stb_ref = Staatsblad.objects.filter(
        staatsblad_type=Staatsblad.StaatsbladType.KKB,
        raw_metadata_xml__icontains=f"Stb. {stb.jaargang}, {stb.nummer}",
    )

    logger.info(kkbs_metadata_xml_stb_ref)

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

    return []
