"""
    parlhist/parlhistnl/management/commands/experiment_inwerkingtredingsbepalingen_find_inwerkingtredingskb.py

    Experiment inwerkingtredingsbepalingen, step 2
    Using the annotated Label Studio JSON dataset, get information on the actual use
    of gedifferentieerde inwerkingtredingsbepalingen.
    Try to find the related inwerkingtredingskb

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
    find_inwerkingtredingskb_via_lido,
    InwerkingtredingsbepalingType,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Experiment inwerkingtredingsbepalingen"""

    help = "Experiment inwerkingtredingsbepalingen"

    def add_arguments(self, parser):
        parser.add_argument(
            "data",
            type=str,
            help="de bestandsnaam van het Label Studio JSON-bestand met de geannoteerde dataset."
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Experiment inwerkingtredingsbepalingen, step 2"""

        with open(options["data"], "rt") as datafile:
            dataset = json.load(datafile)

        gedifferentieerde_inwerkingtredingsbepalingen = []

        for dataset_entry in dataset:
            stbid = dataset_entry["data"]["stb-id"]
            logger.info("Processing %s", stbid)
            try:
                inwerkingtredings_label = dataset_entry["annotations"][0]["result"][0]["value"]["labels"][0]
                logger.info("Has inwerkingtredingsbepalingtype %s", inwerkingtredings_label)

                if inwerkingtredings_label == InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE.value:
                    logger.info("%s has delegatie and differentiatie", stbid)
                    stb: Staatsblad = Staatsblad.objects.get_staatsblad_from_stbid(stbid)

                    try:
                        inwerkingtredingskbs, inwerkingtredingsdata, art_inw, _ = find_inwerkingtredingskb_via_lido(stb)
                        logger.info("(%s) found: %s, %s", stbid, inwerkingtredingskbs, inwerkingtredingsdata)
                        dataset_entry["data"]["inwerkingtredingsinformatie"] = {
                            "inwerkingtredingskbs": [kb.stbid for kb in inwerkingtredingskbs],
                            "inwerkingtredingsdata": [date.strftime("%Y-%m-%d") for date in inwerkingtredingsdata],
                            "artikelen_inwerkingtredingsinformatie": art_inw
                        }
                        gedifferentieerde_inwerkingtredingsbepalingen.append(dataset_entry)
                    except:
                        logger.fatal("!!! WARNING !!! could not find inwerkingtredingsinformation for %s", stbid)
            except IndexError:
                logger.info("No result in annotation for %s, assuming no inwerkingtredingsbepaling", stbid)

        with open(f"experiment-inwerkingtredingsmomenten-{datetime.datetime.now().strftime('%Y-%m-%d_%H%M')}.json", "wt", encoding="utf-8") as resultsfile:
            json.dump(gedifferentieerde_inwerkingtredingsbepalingen, resultsfile)
