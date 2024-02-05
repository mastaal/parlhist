"""
    parlhist/parlhistnl/management/commands/vergaderdag_crawl_full_vergaderjaar.py

    Crawl all vergaderingen of a vergaderjaar.

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging
from typing import Any

from django.core.management import BaseCommand
from django.core.management.base import CommandParser

from parlhistnl.crawler.utils import CrawlerException
from parlhistnl.crawler.vergadering import crawl_vergadering

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Crawl all vergaderingen of a vergaderjaar."""

    help = "Crawl all vergaderingen of a vergaderjaar."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments"""
        parser.add_argument("vergaderjaar", type=str, help="Het vergaderjaar, zonder streepje, zoals 20212022")
        parser.add_argument("--kamer", type=str, choices=["ek", "tk"], default="tk", help="Welke parlementaire kamer, standaard tk")

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Crawl all vergaderingen of a vergaderjaar."""

        previous_errors = 0
        nummer = 1

        while previous_errors <= 10:
            try:
                vergadering = crawl_vergadering(options["vergaderjaar"], nummer, options["kamer"])

                previous_errors = 0

                if vergadering is not None:
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully crawled {vergadering}")  # pylint: disable=no-member
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("Aanhangsel already exists")  # pylint: disable=no-member
                    )
            except CrawlerException:
                previous_errors += 1
                self.stdout.write(
                    self.style.ERROR(f"Couldn't crawl {nummer}")  # pylint: disable=no-member
                )

            nummer += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully crawled vergaderingen in vergaderjaar {options['vergaderjaar']}")  # pylint: disable=no-member
        )
