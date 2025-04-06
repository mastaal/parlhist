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
from typing import Any

from django.core.management import BaseCommand

from parlhistnl.models import Staatsblad
from parlhistnl.utils.inwerkingtredingsbepalingen import (
    find_inwerkingtredingsbepaling,
    InwerkingtredingsbepalingType,
)

logger = logging.getLogger(__name__)


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
            jaargang__in=list(range(1995, 2025)),
        ).order_by("publicatiedatum")

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

            if wet.is_goedkeuringswet_verdrag:
                goedkeuringswet_verdrag += 1

            check_result = find_inwerkingtredingsbepaling(wet)

            labeled_matches = check_result["labeled_matches"]

            resultlist = []
            id_count = 0
            for labeled_match in labeled_matches:
                result = {
                            "id": f"{wet.stbid}-{id_count}",
                            "from_name": "label",
                            "to_name": "text",
                            "type": "labels",
                            "value": {
                                "start": labeled_match["start"],
                                "end": labeled_match["end"],
                                "score": 0.25,
                                "text": labeled_match["text"],
                                "labels": [labeled_match["label"].value],
                            },
                }

                id_count += 1
                resultlist.append(result)

            # These statistics are currently based on the first inwerkingtredingsbepaling found
            if (
                check_result["label"] != InwerkingtredingsbepalingType.ONBEKEND
                and check_result["label"]
                != InwerkingtredingsbepalingType.GEEN_INWERKINGTREDINGSBEPALING
            ):
                if (
                    check_result["label"]
                    == InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
                ):
                    iwtr_d_d += 1
                elif (
                    check_result["label"]
                    == InwerkingtredingsbepalingType.DELEGATIE_ZONDER_DIFFERENTIATIE
                ):
                    iwtr_d_zd += 1
                elif (
                    check_result["label"]
                    == InwerkingtredingsbepalingType.GEEN_DELEGATIE
                ):
                    iwtr_zd_zd += 1
            else:
                print(wet.preferred_url, "No matches found")
                iwtr_onbekend += 1

            prediction = [
                {"model_version": "re-0.0.1", "score": 0.25, "result": resultlist}
            ]

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

        print(f"Totaal wetten: {wetten.count()}")
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
