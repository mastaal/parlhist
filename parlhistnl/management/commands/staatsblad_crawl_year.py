"""
parlhist/parlhistnl/management/commands/staatsblad_crawl_year.py

Crawl a complete year of Staatsblad publications.

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
SPDX-FileCopyrightText: 2025 Martijn Staal <parlhist [at] martijn-staal.nl>
SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import logging
from typing import Any

from django.core.management import BaseCommand
from django.core.management.base import CommandParser

from parlhistnl.crawler.staatsblad import (
    crawl_all_staatsblad_publicaties_in_year,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Crawl a complete year of Staatsblad publications."""

    help = "Crawl a complete year of Staatsblad publications."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments"""
        parser.add_argument("jaargang", type=int)

        parser.add_argument("--update", action="store_true", help="Update")
        parser.add_argument(
            "--queue-tasks", action="store_true", help="Queue tasks using Celery"
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        year = options["jaargang"]

        self.stdout.write(self.style.NOTICE(f"Crawling year {year}"))
        stbs = crawl_all_staatsblad_publicaties_in_year(
            year, update=options["update"], queue_tasks=options["queue_tasks"]
        )

        self.stdout.write(self.style.SUCCESS(f"Crawled {stbs}"))
