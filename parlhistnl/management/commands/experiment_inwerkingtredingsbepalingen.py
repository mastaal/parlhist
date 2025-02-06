"""
    parlhist/parlhistnl/management/commands/experiment_inwerkingtredingsbepalingen.py

    Experiment inwerkingtredingsbepalingen
    Simple regex-based recognition of inwerkingtredingsbepalingen in the Staatsblad.
    Outputs to a Label Studio JSON file with predicted labels.

    Copyright 2025 Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import json
import logging
import re
from typing import Any

from django.core.management import BaseCommand

from parlhistnl.models import Staatsblad

logger = logging.getLogger(__name__)
iwt_re: re.Pattern = re.compile(
    r"(de\s+artikelen\s+van\s+deze\s+(rijks)?wet\s+treden|deze\s+(rijks)?wet\s+treedt)(,\s+onder\s+toepassing\s+van\s+artikel\s+12,\s+eerste lid,\s+van\s+de\s+Wet\s+raadgevend\s+referendum,)?\s+in\s+werking[\w,\s]+.(\s*indien[\w,\s]+.)?",
    re.IGNORECASE,
)

kb_re: re.Pattern = re.compile(
    r"bij\s+koninklijk\s+besluit\s+te\s+bepalen\s+tijdstip", re.IGNORECASE
)
dif_re: re.Pattern = re.compile(
    r"verschillend\s+kan\s+worden\s+vastgesteld", re.IGNORECASE
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

        for wet in wetten:

            cleaned_tekst1 = wet.tekst.replace("\xa0", " ")
            cleaned_tekst = f"{wet.preferred_url}\n{cleaned_tekst1}"

            matches = list(iwt_re.finditer(cleaned_tekst))

            if len(matches) == 1:
                print(wet.preferred_url, matches[0].group(0))
                m = matches[0]

                # find if it contains KB
                matcheskb = list(kb_re.finditer(m.group(0)))

                matchesdif = list(dif_re.finditer(m.group(0)))
                if len(matcheskb) > 0 and len(matchesdif) > 0:
                    labels = [
                        "Inwerkingtredingsbepaling met delegatie en differentiatie"
                    ]
                    iwtr_d_d += 1
                elif len(matcheskb) > 0 and len(matchesdif) == 0:
                    labels = [
                        "Inwerkgintredingsbepaling met delegatie zonder differentiatie"
                    ]
                    iwtr_d_zd += 1
                else:
                    labels = ["Inwerkingtredingsbepaling zonder delegatie"]
                    iwtr_zd_zd += 1

                resultlist = [
                    {
                        "id": "0",
                        "from_name": "label",
                        "to_name": "text",
                        "type": "labels",
                        "value": {
                            "start": m.start(0),
                            "end": m.end(0),
                            "score": 0.25,
                            "text": m.group(0),
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
                        "text": cleaned_tekst,
                        "stb-id": f"stb-{wet.jaargang}-{wet.nummer}",
                    },
                    "predictions": prediction,
                }
            )

        with open("task.json", "wt", encoding="utf-8") as jsonfile:
            json.dump(data, jsonfile)

        print("Dumped wetten:", len(data))
        print(iwtr_d_d, iwtr_d_zd, iwtr_zd_zd, iwtr_onbekend)
