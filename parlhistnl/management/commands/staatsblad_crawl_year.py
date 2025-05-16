"""
    parlhist/parlhistnl/management/commands/staatsblad_crawl_year.py

    Crawl a complete year of Staatsblad publications.

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
    SPDX-FileCopyrightText: 2025 Martijn Staal <parlhist [at] martijn-staal.nl>
"""

import logging
from typing import Any

from django.core.management import BaseCommand
from django.core.management.base import CommandParser

from parlhistnl.crawler.staatsblad import (
    crawl_all_staatsblad_publicaties_within_koop_sru_query,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Crawl a complete year of Staatsblad publications."""

    help = "Crawl a complete year of Staatsblad publications."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments"""
        parser.add_argument("jaargang", type=int)

        parser.add_argument("--update", action="store_true", help="Update")

    def handle(self, *args: Any, **options: Any) -> str | None:
        year = options["jaargang"]

        self.stdout.write(self.style.NOTICE(f"Crawling year {year}"))
        stbs = crawl_all_staatsblad_publicaties_within_koop_sru_query(
            f"(w.publicatienaam=Staatsblad AND dt.date >= {year}-01-01 AND dt.date <= {year}-12-31)",
            update=options["update"],
        )

        self.stdout.write(self.style.SUCCESS(f"Crawled {stbs}"))
