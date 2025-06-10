"""
parlhist/parlhistnl/management/commands/kamerstukken_crawl_year.py.py

Crawl all Kamerstukken in a calendar year (e.g., 2020-01-01 through 2020-12-31).

Copyright 2024, 2025 Martijn Staal <parlhist [at] martijn-staal.nl>

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
SPDX-FileCopyrightText: 2024-2025 Martijn Staal <parlhist [at] martijn-staal.nl>
SPDX-FileCopyrightText: 2024-2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import datetime
import logging
from typing import Any

from django.core.management import BaseCommand
from django.core.management.base import CommandParser

from parlhistnl.crawler.kamerstuk import crawl_all_kamerstukken_within_koop_sru_query

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Crawl all Kamerstukken in a calendar year (e.g., 2020-01-01 through 2020-12-31)."""

    help = "Crawl all Kamerstukken in a calendar year (e.g., 2020-01-01 through 2020-12-31)."

    def add_arguments(self, parser: CommandParser) -> None:

        current_year = datetime.date.today().year

        """Add arguments"""
        parser.add_argument(
            "year",
            type=int,
            choices=list(range(1995, current_year + 1)),
            default=2020,
            help="Which calendar year to crawl the kamerstukken of",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update Kamerstukken already in the database",
        )
        parser.add_argument(
            "--queue-tasks", action="store_true", help="Queue tasks using Celery"
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Crawl one Vergadering and all its subitems"""

        year = options["year"]

        koop_sru_query = f"(c.product-area==officielepublicaties AND dt.type=Kamerstuk AND dt.date >={year}-01-01 AND dt.date <= {year}-12-31)"

        kamerstukken = crawl_all_kamerstukken_within_koop_sru_query(
            koop_sru_query, update=options["update"], queue_tasks=options["queue_tasks"]
        )

        logger.info(
            "Crawling using management command with koop query %s with update=%s",
            koop_sru_query,
            options["update"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully crawled kamerstukken using KOOP SRU query {koop_sru_query}"
            )  # pylint: disable=no-member
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Crawled the following subitems:"
            )  # pylint: disable=no-member
        )
        for kamerstuk in kamerstukken:
            self.stdout.write(
                self.style.SUCCESS(f"* {kamerstuk}")  # pylint: disable=no-member
            )
