"""
parlhist/parlhistnl/management/commands/handelingen_crawl_vergaderjaar.py

Crawl a complete vergaderjaar of the Handelingen.

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
SPDX-FileCopyrightText: 2025 Martijn Staal <parlhist [at] martijn-staal.nl>
SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import logging
from typing import Any

from django.core.management import BaseCommand
from django.core.management.base import CommandParser

from parlhistnl.crawler.handeling import crawl_all_handelingen_in_vergaderjaar

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Crawl a complete calendar year of Handelingen."""

    help = "Crawl a complete calendar year of Handelingen."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments"""
        parser.add_argument("vergaderjaar", type=str, help="Het kalenderjaar om de publicaties in de Handelingen te crawlen, bijvoorbeeld 2005-2006.")

        parser.add_argument(
            "--queue-tasks", action="store_true", help="Queue tasks using Celery"
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        year = options["vergaderjaar"]

        self.stdout.write(self.style.NOTICE(f"Crawling year {year}"))
        handelingen = crawl_all_handelingen_in_vergaderjaar(
            year, queue_tasks=options["queue_tasks"]
        )

        self.stdout.write(self.style.SUCCESS(f"Crawled {handelingen}"))
