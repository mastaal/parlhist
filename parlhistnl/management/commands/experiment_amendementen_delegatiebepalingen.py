"""
    parlhist/parlhistnl/management/commands/experiment_amendementen_delegatiebepalingen.py

    Regex-based experiment to identify amendments similar to Kamerstukken II 2023/24, 36.496, nr. 54
    (https://zoek.officielebekendmakingen.nl/kst-36496-54.html)

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-FileCopyrightText: 2024-2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
    SPDX-License-Identifier: EUPL-1.2
"""

import csv
import datetime
import json
import logging
import re
from typing import Any

from django.db.models import QuerySet
from django.core.management import BaseCommand

from parlhistnl.models import Kamerstuk

logger = logging.getLogger(__name__)

DELEGATIEBEPALING_PATTERN = r"(bij(\s+of\s+krachtens)?\s+de\s+algemene\s+maatregel\s+van\s+(rijks)?bestuur)|((bij\s+de\s+ministeriële\s+regeling)|(bij\s+de\s+regeling\s+van\s+onze\s+minister))"
re_amvb_mr = re.compile(DELEGATIEBEPALING_PATTERN, re.IGNORECASE)

WORDT_BEPAALD_PATTERN = (
    r"wordt(\s+in\s+ieder\s+geval\s+|\s+ten\s+minste)?\s+(bepaald|gewaarborgd)"
)
re_wordt_bepaald = re.compile(WORDT_BEPAALD_PATTERN, re.IGNORECASE)

TOELICHTING_PATTERN = r"Toelichting"
re_toelichting = re.compile(TOELICHTING_PATTERN)

BASE_FILENAME = f"experiment-amendementen-delegatiebepalingen-{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}"


class Command(BaseCommand):
    """Experiment amendementen en delegatiebepalingen"""

    help = "Experiment amendementen en delegatiebepalingen"

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Experiment amendementen en delegatiebepalingen"""

        end_date = datetime.date(2024, 4, 25)

        amendementen: QuerySet[Kamerstuk] = Kamerstuk.objects.filter(
            kamerstuktype=Kamerstuk.KamerstukType.AMENDEMENT,
            documentdatum__lte=end_date,
        )
        logger.info(
            "Found %s amendementen that have a recorded date before %s",
            amendementen.count(),
            end_date.strftime("%Y-%m-%d"),
        )

        # First pass: using a django query, check if the amendment possibly contains a delegatiebepaling
        # Based on Ar 2.26 (amvb) (https://wetten.overheid.nl/jci1.3:c:BWBR0005730&hoofdstuk=2&paragraaf=2.4&aanwijzing=2.26&z=2024-07-01&g=2024-07-01)
        # and Ar 2.28 (ministeriële regeling), but note the 'de' added to it, which is used to refer to the previously-existing delegatiebepaling.
        amendments_mention_amvb_mr = amendementen.filter(
            tekst__iregex=DELEGATIEBEPALING_PATTERN
        )

        logger.info(
            "Found %s amendementen that seem to contain a delegatiebepaling",
            amendments_mention_amvb_mr.count(),
        )

        # Second filter: are they possibly similar, based on a regex-based Django database query
        amendments_possibly_similar = amendments_mention_amvb_mr.filter(
            tekst__iregex=WORDT_BEPAALD_PATTERN
        ).order_by("documentdatum", "hoofddossier__dossiernummer", "ondernummer")
        logger.info(
            "Found %s amendementen possibly similar to kst-36496-54",
            amendments_possibly_similar.count(),
        )

        # Since the "tekst" field in the database contains the complete text of both the amendment and the explanation,
        # our previously found matches could actually be text pieces in the explanation and not in the amendement itself.
        # We are however only interested in the text of the amendment itself. To further decrease the amount of false positive
        # matches, we can split up the text of the amendments on the Toelichting heading, in order to limit our search to
        # the amendment text. However, this Toelichting heading is not consistently readable as such in the metadata,
        # and is thus error-prone. A safe approach is to check if our TOELICHTING_PATTERN has strictly one match, and
        # if so, split on this pattern. If we couldn't split, we sort the amendment separately for manual inspection

        # These amendments could be splitted on TOELICHTING_PATTERN and satisfy our two other patterns.
        amendments_with_both_matches_in_amendment_text = []

        # These amendments could be splitted on TOELICHTING_PATTERN and satisfy the DELEGATIEBEPALING_PATTERN, but not our other pattern.
        amendments_with_only_match_amvb_mr_in_amendment_text = []

        # These amendments could not be splitted.
        amendments_that_could_not_be_split = []

        # These amendments could be splitted but do not satisfy either of our two other patterns.
        rejected_amendments_after_in_text_filter = []

        for amendment in amendments_mention_amvb_mr:
            # logger.info("Checking %s", amendment)

            toelichting_matches = re_toelichting.findall(amendment.tekst)

            if len(toelichting_matches) == 1:
                # We found exactly one match for the TOELICHTING_PATTERN, assume we can safely split.
                text_parts = re_toelichting.split(amendment.tekst)

                amendment_text = text_parts[0]

                if len(re_amvb_mr.findall(amendment_text)) > 0:
                    if len(re_wordt_bepaald.findall(amendment_text)) > 0:
                        # Matches both
                        logger.info("Seems similar %s, %s", amendment, amendment.url())
                        amendments_with_both_matches_in_amendment_text.append(amendment)
                    else:
                        # Match 1 but not 2
                        logger.info("Only matches DELEGATIEBEPALING_PATTERN %s, %s", amendment, amendment.url())
                        amendments_with_only_match_amvb_mr_in_amendment_text.append(amendment)
                else:
                    # Matches neither
                    rejected_amendments_after_in_text_filter.append(amendment)
            else:
                logger.info(
                    "%s could not be split because there was not exactly one TOELICHTING_PATTERN match",
                    amendment,
                )
                logger.debug("Found %s", toelichting_matches)
                amendments_that_could_not_be_split.append(amendment)

        logger.info(
            "Rejected %s amendments, could not split %s amendments, with only amvb_mr match %s, might be similar %s amendments",
            len(rejected_amendments_after_in_text_filter),
            len(amendments_that_could_not_be_split),
            len(amendments_with_only_match_amvb_mr_in_amendment_text),
            len(amendments_with_both_matches_in_amendment_text),
        )

        with open(f"{BASE_FILENAME}-pass-1.csv", "wt", encoding="utf-8") as csv_file:
            writer = csv.writer(
                csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )

            writer.writerow(["dossier", "ondernummer", "datum", "url", "titel"])

            for amendment in amendments_mention_amvb_mr.order_by(
                "documentdatum", "hoofddossier__dossiernummer", "ondernummer"
            ):
                writer.writerow(
                    [
                        amendment.hoofddossier.dossiernummer,
                        amendment.ondernummer,
                        amendment.documentdatum,
                        amendment.url(),
                        amendment.documenttitel,
                    ]
                )

        # Store all amendments that were found in amendments_possibly_similar, so which are accepted based on
        # our two Django database queries, but before inspection of the split text
        with open(f"{BASE_FILENAME}-pass-2.csv", "wt", encoding="utf-8") as csv_file:
            writer = csv.writer(
                csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )

            writer.writerow(["dossier", "ondernummer", "datum", "url", "titel"])

            for amendment in amendments_possibly_similar.order_by(
                "documentdatum", "hoofddossier__dossiernummer", "ondernummer"
            ):
                writer.writerow(
                    [
                        amendment.hoofddossier.dossiernummer,
                        amendment.ondernummer,
                        amendment.documentdatum,
                        amendment.url(),
                        amendment.documenttitel,
                    ]
                )

        with open(f"{BASE_FILENAME}-pass-3.csv", "wt", encoding="utf-8") as csv_file:
            writer = csv.writer(
                csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )

            writer.writerow(
                ["dossier", "ondernummer", "datum", "url", "titel", "label"]
            )

            for amendment in amendments_with_both_matches_in_amendment_text:
                writer.writerow(
                    [
                        amendment.hoofddossier.dossiernummer,
                        amendment.ondernummer,
                        amendment.documentdatum,
                        amendment.url(),
                        amendment.documenttitel,
                        "Matches both patterns in amendment text",
                    ]
                )

            for amendment in amendments_with_only_match_amvb_mr_in_amendment_text:
                writer.writerow(
                    [
                        amendment.hoofddossier.dossiernummer,
                        amendment.ondernummer,
                        amendment.documentdatum,
                        amendment.url(),
                        amendment.documenttitel,
                        "Only matches delegatiebepaling pattern in amendment text",
                    ]
                )

            for amendment in amendments_that_could_not_be_split:
                writer.writerow(
                    [
                        amendment.hoofddossier.dossiernummer,
                        amendment.ondernummer,
                        amendment.documentdatum,
                        amendment.url(),
                        amendment.documenttitel,
                        "Text could not be split into amendment text and explanation parts",
                    ]
                )

            for amendment in rejected_amendments_after_in_text_filter:
                writer.writerow(
                    [
                        amendment.hoofddossier.dossiernummer,
                        amendment.ondernummer,
                        amendment.documentdatum,
                        amendment.url(),
                        amendment.documenttitel,
                        "Rejected after inspection of amendment text only",
                    ]
                )

        with open(
            f"{BASE_FILENAME}-pass-3-full-text.csv", "wt", encoding="utf-8"
        ) as csv_file:
            writer = csv.writer(
                csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )

            writer.writerow(
                ["dossier", "ondernummer", "datum", "url", "titel", "label", "tekst"]
            )

            for amendment in amendments_with_both_matches_in_amendment_text:
                writer.writerow(
                    [
                        amendment.hoofddossier.dossiernummer,
                        amendment.ondernummer,
                        amendment.documentdatum,
                        amendment.url(),
                        amendment.documenttitel,
                        "Matches both patterns in amendment text",
                        amendment.tekst,
                    ]
                )

            for amendment in amendments_with_only_match_amvb_mr_in_amendment_text:
                writer.writerow(
                    [
                        amendment.hoofddossier.dossiernummer,
                        amendment.ondernummer,
                        amendment.documentdatum,
                        amendment.url(),
                        amendment.documenttitel,
                        "Only matches delegatiebepaling pattern in amendment text",
                        amendment.tekst,
                    ]
                )

        with open(
            f"{BASE_FILENAME}-pass-3-results.json", "wt", encoding="utf-8"
        ) as json_file:
            amendementen_pass_3_json = []

            amendment: Kamerstuk
            for amendment in (
                amendments_with_both_matches_in_amendment_text
                + amendments_with_only_match_amvb_mr_in_amendment_text
                + amendments_that_could_not_be_split
                + rejected_amendments_after_in_text_filter
            ):
                amendementen_pass_3_json.append(
                    {
                        "dossiernummer": amendment.hoofddossier.dossiernummer,
                        "ondernummer": amendment.ondernummer,
                        "documenttitel": amendment.documenttitel,
                        "documentdatum": str(amendment.documentdatum),
                        "vergaderjaar": amendment.vergaderjaar,
                        "kamer": amendment.kamer,
                        "indiener": amendment.indiener,
                        "tekst": amendment.tekst,
                        "raw_html": amendment.raw_html,
                        "raw_metadata_xml": amendment.raw_metadata_xml,
                        "kamerstuktype": amendment.kamerstuktype,
                        "bijgewerkt_op": str(amendment.bijgewerkt_op),
                        "toegevoegd_op": str(amendment.toegevoegd_op),
                    }
                )

            json.dump(amendementen_pass_3_json, json_file)
