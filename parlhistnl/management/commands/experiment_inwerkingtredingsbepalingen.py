"""
    parlhist/parlhistnl/management/commands/experiment_inwerkingtredingsbepalingen.py

    Experiment inwerkingtredingsbepalingen
    Simple regex-based recognition of inwerkingtredingsbepalingen in the Staatsblad.
    Outputs to a Label Studio JSON file with predicted labels.

    Copyright 2025 Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import datetime
import json
import logging
import re
from typing import Any

from django.core.management import BaseCommand

from parlhistnl.models import Staatsblad
from parlhistnl.utils.inwerkingtredingsbepalingen import (
    find_inwerkingtredingsbepaling,
    InwerkingtredingsbepalingType,
)

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


class Command(BaseCommand):
    """Experiment inwerkingtredingsbepalingen"""

    help = "Experiment inwerkingtredingsbepalingen"

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Export data for label studio format"""

        wetten = Staatsblad.objects.filter(
            staatsblad_type__in=[
                Staatsblad.StaatsbladType.WET,
                Staatsblad.StaatsbladType.RIJKSWET,
            ],
            jaargang__gte=1995,
        )
        # wetten = Staatsblad.objects.filter(staatsblad_type=Staatsblad.StaatsbladType.WET, jaargang__gte=1995)

        logger.info("Found %s wetten", wetten.count())

        data = []
        iwtr_d_d = 0
        iwtr_d_zd = 0
        iwtr_zd_zd = 0
        iwtr_onbekend = 0

        # There are some special cases which never have an inwerkingtredingsbepaling
        vaststellingswet_grondwetswijziging = 0
        goedkeuringswet_verdrag = 0

        for wet in wetten:

            # Handle special cases which never contain a inwerkingtredingsbepaling
            if wet.is_vaststelling_grond_grondwetswijziging:
                vaststellingswet_grondwetswijziging += 1
                continue

            if wet.is_goedkeuringswet_verdrag:
                goedkeuringswet_verdrag += 1

            check_result = find_inwerkingtredingsbepaling(wet)

            if (
                check_result["label"] != InwerkingtredingsbepalingType.ONBEKEND
                and check_result
                != InwerkingtredingsbepalingType.GEEN_INWERKINGTREDINGSBEPALING
            ):
                if (
                    check_result["label"]
                    == InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
                ):
                    labels = [
                        "Inwerkingtredingsbepaling met delegatie en differentiatie"
                    ]
                    iwtr_d_d += 1
                elif (
                    check_result["label"]
                    == InwerkingtredingsbepalingType.DELEGATIE_ZONDER_DIFFERENTIATIE
                ):
                    labels = [
                        "Inwerkgintredingsbepaling met delegatie zonder differentiatie"
                    ]
                    iwtr_d_zd += 1
                elif (
                    check_result["label"]
                    == InwerkingtredingsbepalingType.GEEN_DELEGATIE
                ):
                    labels = ["Inwerkingtredingsbepaling zonder delegatie"]
                    iwtr_zd_zd += 1

                resultlist = [
                    {
                        "id": "0",
                        "from_name": "label",
                        "to_name": "text",
                        "type": "labels",
                        "value": {
                            "start": check_result["start"],
                            "end": check_result["end"],
                            "score": 0.25,
                            "text": check_result["text"],
                            "labels": labels,
                        },
                    }
                ]

                prediction = [
                    {"model_version": "re-0.0.1", "score": 0.25, "result": resultlist}
                ]
            else:
                print(wet.preferred_url, "No matches found")
                resultlist = []
                prediction = []
                iwtr_onbekend += 1

            data.append(
                {
                    "id": f"stb-{wet.jaargang}-{wet.nummer}",
                    "data": {
                        "text": check_result["cleaned_text"],
                        "stb-id": f"stb-{wet.jaargang}-{wet.nummer}",
                    },
                    "predictions": prediction,
                }
            )

        with open(
            f"experiment-inwerkingtredingsbepalingen-task-{datetime.datetime.now().strftime('%Y-%m-%d_%H%M')}.json",
            "wt",
            encoding="utf-8",
        ) as jsonfile:
            json.dump(data, jsonfile)

        print("Dumped wetten:", len(data))
        print(f"inwerkingtreding met delegatie, met differentiatie: {iwtr_d_d}")
        print(f"inwerkingtreding met delegatie, zonder differentiatie: {iwtr_d_zd}")
        print(f"inwerkingtreding zonder delegatie: {iwtr_zd_zd}")
        print(f"goedkeuringswet verdrag: {goedkeuringswet_verdrag}")
        print(
            f"vaststellingswet grondwetwijziging: {vaststellingswet_grondwetswijziging}"
        )
        print(f"inwerkingtreding type onbekend: {iwtr_onbekend}")
        print(iwtr_d_d, iwtr_d_zd, iwtr_zd_zd, iwtr_onbekend)
