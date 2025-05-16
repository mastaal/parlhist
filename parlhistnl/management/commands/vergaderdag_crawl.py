"""
    parlhist/parlhistnl/management/commands/vergaderdag_crawl.py

    Crawl one Vergadering and all its subitems

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
    SPDX-FileCopyrightText: 2023 Martijn Staal <parlhist [at] martijn-staal.nl>
    SPDX-FileCopyrightText: 2024 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import logging
from typing import Any

from django.core.management import BaseCommand
from django.core.management.base import CommandParser

from parlhistnl.crawler.vergadering import crawl_vergadering
from parlhistnl.models import Vergadering, Handeling

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Crawl one Vergadering and all its subitems"""

    help = "Crawl one Vergadering and all its subitems"

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments"""
        parser.add_argument(
            "vergaderjaar",
            type=str,
            help="Het vergaderjaar, zonder streepje, zoals 20212022",
        )
        parser.add_argument(
            "nummer", type=int, help="Het nummer van het aanhangsel, zoals 42"
        )
        parser.add_argument(
            "--kamer",
            type=str,
            choices=["ek", "tk"],
            default="tk",
            help="Welke parlementaire kamer, standaard tk",
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Crawl one Vergadering and all its subitems"""

        vergaderdag: Vergadering = crawl_vergadering(
            options["vergaderjaar"], options["nummer"], options["kamer"]
        )

        handelingen = Handeling.objects.filter(vergadering=vergaderdag)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {vergaderdag}"
            )  # pylint: disable=no-member
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Crawled the following subitems:"
            )  # pylint: disable=no-member
        )
        for handeling in handelingen:
            self.stdout.write(
                self.style.SUCCESS(f"* {handeling}")  # pylint: disable=no-member
            )
