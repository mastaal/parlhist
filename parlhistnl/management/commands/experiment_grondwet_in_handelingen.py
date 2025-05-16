"""
    parlhist/parlhistnl/management/commands/experiment_grondwet_in_handelingen.py

    Experiment Grondwet in Handelingen
    Simple regex-based recognition of mentions of the constitution in parliamentary proceedings.

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
    SPDX-FileCopyrightText: Copyright 2023-2024 Martijn Staal <parlhist [at] martijn-staal.nl>
    SPDX-FileCopyrightText: Copyright 2024 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import csv
import logging
import re
from typing import Any

from django.db.models import QuerySet
from django.core.management import BaseCommand
from django.core.management.base import CommandParser
from django.utils import timezone

from parlhistnl.models import Handeling, Kamerstuk

logger = logging.getLogger(__name__)
re_constitutie: re.Pattern = re.compile(
    r"\w*grondwet\w*|\w*constituti\w*", re.IGNORECASE
)
re_evrm: re.Pattern = re.compile(
    r"EVRM|Europees Verdrag tot Bescherming van de Rechten van de Mens", re.IGNORECASE
)
KAMERSTUKTYPES: list[str] = list(
    Kamerstuk.objects.all().values_list("kamerstuktype", flat=True).distinct()
)


def get_doc_match_counts(kamerstuk: Kamerstuk, pattern: re.Pattern) -> int:
    """Get the number of pattern matches in the text of some kamerstuk"""
    return len(pattern.findall(kamerstuk.tekst))


def get_handeling_statistics(handeling: Handeling, is_prefiltered: bool) -> dict:
    """Get the statistics for one handeling"""

    results = {}

    if is_prefiltered:
        logger.info(
            "Handeling %s is in prefilterd set, checking the handeling itself",
            handeling,
        )
        # TODO: Filter per fractie/spreekbeurt
        matches = re_constitutie.findall(handeling.tekst)
        # print(matches)

        if len(matches) > 0:
            results["matches_per_handeling"] = matches
        else:
            results["matches_per_handeling"] = []
    else:
        results["matches_per_handeling"] = []

    # initialize matches per type to zero:
    results["related_kamerstukken_matches_per_kamerstuktype"] = dict()
    for ksttype in KAMERSTUKTYPES:
        results["related_kamerstukken_matches_per_kamerstuktype"][ksttype] = 0

    # Sadly, it's not possible to filter a queryset after a union...
    behandelde_kamerstukken_1 = handeling.behandelde_kamerstukken.all()
    behandelde_kamerstukken_2 = Kamerstuk.objects.filter(
        hoofddossier__in=handeling.behandelde_kamerstukdossiers.all()
    )
    total_documents = (
        behandelde_kamerstukken_1.count() + behandelde_kamerstukken_2.count()
    )
    results["related_kamerstukken_totaal"] = total_documents
    grondwet_matching_documents: QuerySet[Kamerstuk] = behandelde_kamerstukken_1.filter(
        tekst__iregex=r"grondwet\w*|constituti\w*"
    ).union(
        behandelde_kamerstukken_2.filter(tekst__iregex=r"grondwet\w*|constituti\w*")
    )
    matching_documents_count = grondwet_matching_documents.count()
    results["related_kamerstukken_met_een_match"] = matching_documents_count
    results["related_kamerstukken_rvs_evrm"] = 0

    for doc in grondwet_matching_documents:
        doc_num_matches = len(re_constitutie.findall(doc.tekst))
        results["related_kamerstukken_matches_per_kamerstuktype"][
            doc.kamerstuktype
        ] += doc_num_matches
        if doc_num_matches > 0:
            logger.debug("Found nonzero matches in %s", doc)

    rvs_evrm_matching_documents: QuerySet[Kamerstuk] = behandelde_kamerstukken_1.filter(
        kamerstuktype=Kamerstuk.KamerstukType.ADVIES_RVS,
        tekst__iregex=r"EVRM|Europees Verdrag tot Bescherming van de Rechten van de Mens",
    ).union(
        behandelde_kamerstukken_2.filter(
            kamerstuktype=Kamerstuk.KamerstukType.ADVIES_RVS,
            tekst__iregex=r"EVRM|Europees Verdrag tot Bescherming van de Rechten van de Mens",
        )
    )
    for doc in rvs_evrm_matching_documents:
        results["related_kamerstukken_rvs_evrm"] += len(re_evrm.findall(doc.tekst))

    # Calculate totals
    results["related_kamerstukken_matches_per_kamerstuktype"]["Totaal"] = 0
    for ksttype in KAMERSTUKTYPES:
        results["related_kamerstukken_matches_per_kamerstuktype"]["Totaal"] += results[
            "related_kamerstukken_matches_per_kamerstuktype"
        ][ksttype]

    logger.info(
        "%s, aantal documenten met ten minste 1 match: %s (totaal %s bijbehorende documenten)",
        handeling,
        matching_documents_count,
        total_documents,
    )
    logger.info(results["related_kamerstukken_matches_per_kamerstuktype"])

    return results


class Command(BaseCommand):
    """Experiment 2"""

    help = "Experiment 2"

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments"""

        parser.add_argument(
            "--kamer",
            type=str,
            choices=["ek", "tk"],
            default="tk",
            help="Welke parlementaire kamer, standaard tk",
        )
        parser.add_argument(
            "--vergaderjaar",
            type=str,
            help="Het vergaderjaar om het experiment tot te beperken. Als er geen vergaderjaar wordt gegeven, worden simpelweg alle handelingen in de database doorzocht.",
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Experiment 1

        Find all matches to the regex in the Handelingen
        """

        vergaderjaar = None

        if options["vergaderjaar"] is not None:
            totaal_handelingen = Handeling.objects.filter(  # pylint: disable=no-member
                vergadering__vergaderjaar=options["vergaderjaar"],
                vergadering__kamer=options["kamer"],
            )
            totaal_handelingen_count = totaal_handelingen.count()
            vergaderjaren: list[str] = [options["vergaderjaar"]]
            handelingen_prefiltered_set = (
                Handeling.objects.filter(  # pylint: disable=no-member
                    vergadering__vergaderjaar=options["vergaderjaar"],
                    vergadering__kamer=options["kamer"],
                    tekst__iregex=r"grondwet\w*|constituti\w*",
                )
            )
            vergaderjaar = options["vergaderjaar"]
        else:
            totaal_handelingen = Handeling.objects.filter(
                vergadering__kamer=options["kamer"]
            )
            totaal_handelingen_count = (
                totaal_handelingen.count()
            )  # pylint: disable=no-member
            vergaderjaren: list[str] = list(
                Handeling.objects.filter(vergadering__kamer=options["kamer"])
                .values_list("vergadering__vergaderjaar", flat=True)
                .distinct()
            )
            handelingen_prefiltered_set = (
                Handeling.objects.filter(  # pylint: disable=no-member
                    vergadering__kamer=options["kamer"],
                    tekst__iregex=r"grondwet\w*|constituti\w*",
                )
            )

        total_handelingen_prefiltered = handelingen_prefiltered_set.count()
        totaal_handelingen_met_een_match = 0

        matches_per_handeling = {}
        related_kamerstukken_totaal_per_handeling = {}
        related_kamerstukken_met_een_match_per_handeling = {}
        related_kamerstukken_matches_per_kamerstuktype_per_handeling = {}
        related_kamerstukken_rvs_evrm = {}

        handeling: Handeling

        for handeling in totaal_handelingen:
            results = get_handeling_statistics(
                handeling, handeling in handelingen_prefiltered_set
            )
            related_kamerstukken_totaal_per_handeling[handeling] = results[
                "related_kamerstukken_totaal"
            ]
            matches_per_handeling[handeling] = results["matches_per_handeling"]
            if len(results["matches_per_handeling"]) > 0:
                totaal_handelingen_met_een_match += 1
            related_kamerstukken_matches_per_kamerstuktype_per_handeling[handeling] = (
                results["related_kamerstukken_matches_per_kamerstuktype"]
            )
            related_kamerstukken_met_een_match_per_handeling[handeling] = results[
                "related_kamerstukken_met_een_match"
            ]
            related_kamerstukken_rvs_evrm[handeling] = results[
                "related_kamerstukken_rvs_evrm"
            ]

        logger.info(
            f"Found {totaal_handelingen_met_een_match} in {totaal_handelingen_count} handelingen ({total_handelingen_prefiltered} in prefilter set)"
        )

        now = timezone.now()
        if vergaderjaar is not None:
            base_filename = f"experiment_1_{options['kamer']}_{options['vergaderjaar']}_{now.strftime('%Y-%m-%d_%H%M')}"
        else:
            base_filename = (
                f"experiment_1_{options['kamer']}_{now.strftime('%Y-%m-%d_%H%M')}"
            )

        with open(f"{base_filename}_results.csv", "wt", encoding="utf-8") as csvfile:
            writer = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )
            writer.writerow(["Experiment 2", f"Kamer: {options['kamer']}"])
            writer.writerow(["Vergaderjaren"] + vergaderjaren)
            writer.writerow(["Aantal gevonden handelingen", totaal_handelingen_count])
            writer.writerow(
                ["Aantal handelingen met een match", totaal_handelingen_met_een_match]
            )

        with open(
            f"{base_filename}_statistieken_per_handeling.csv", "wt", encoding="utf-8"
        ) as csvfile:
            writer = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )
            writer.writerow(
                [
                    "Handeling",
                    "Titel",
                    "Handelingtype",
                    "Aantal grondwetmatches in handelingen",
                    "Totaal aantal matches in alle behandelde kamerstukken",
                    "Aantal behandelde kamerstukken met ten minste 1 grondwetmatch",
                    "Aantal keren dat het EVRM genoemd is in een bijbehorend RvS-advies",
                ]
                + [
                    f"Totaal aantal matches in kamerstukken van type {ksttype}"
                    for ksttype in KAMERSTUKTYPES
                ]
            )

            for handeling in totaal_handelingen:
                writer.writerow(
                    [
                        handeling,
                        handeling.titel,
                        handeling.handelingtype,
                        len(matches_per_handeling[handeling]),
                        related_kamerstukken_matches_per_kamerstuktype_per_handeling[
                            handeling
                        ]["Totaal"],
                        related_kamerstukken_met_een_match_per_handeling[handeling],
                        related_kamerstukken_rvs_evrm[handeling],
                    ]
                    + [
                        related_kamerstukken_matches_per_kamerstuktype_per_handeling[
                            handeling
                        ][ksttype]
                        for ksttype in KAMERSTUKTYPES
                    ]
                )

        with open(f"{base_filename}_matches.csv", "w", encoding="utf-8") as csvfile:
            writer = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )
            writer.writerow(
                [
                    "Handeling met een match",
                    "Naam",
                    "Type",
                    "URL",
                    "Aantal matches",
                    "Matches",
                ]
            )
            for handeling, matches in matches_per_handeling.items():
                if (len(matches)) > 0:
                    writer.writerow(
                        [
                            handeling,
                            handeling.titel,
                            handeling.handelingtype,
                            handeling.url(),
                            len(matches),
                        ]
                        + matches
                    )

        with open(
            f"{base_filename}_behandelde_kamerstukken.csv", "wt", encoding="utf-8"
        ) as csvfile:
            writer = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )

            for handeling in totaal_handelingen:
                writer.writerow(
                    [handeling] + list(handeling.behandelde_kamerstukken.all())
                )

        with open(
            f"{base_filename}_behandelde_kamerstukdossiers.csv", "wt", encoding="utf-8"
        ) as csvfile:
            writer = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )

            for handeling in totaal_handelingen:
                writer.writerow(
                    [handeling] + list(handeling.behandelde_kamerstukdossiers.all())
                )
