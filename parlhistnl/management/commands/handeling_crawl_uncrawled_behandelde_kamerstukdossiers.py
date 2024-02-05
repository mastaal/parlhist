"""
    parlhist/parlhistnl/management/commands/handeling_crawl_uncrawled_behandelde_kamerstukdossiers.py

    Crawl one Vergadering and all its subitems

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging
from typing import Any

from django.core.management import BaseCommand

from parlhistnl.crawler.handeling import crawl_uncrawled_behandelde_kamerstukdossiers
from parlhistnl.models import Handeling

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Crawl one Vergadering and all its subitems"""

    help = "Crawl one Vergadering and all its subitems"

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Crawl one Vergadering and all its subitems"""

        handelingen = Handeling.objects.exclude(data__uncrawled__behandelde_kamerstukdossiers=[])

        for handeling in handelingen:
            logger.info("Crawling behandelde kamerstukken for %s", handeling)

            try:
                kamerstukken = crawl_uncrawled_behandelde_kamerstukdossiers(handeling)

                self.stdout.write(
                    self.style.SUCCESS(f"Successfully created {kamerstukken}")  # pylint: disable=no-member
                )
            except Exception as exc:
                logger.critical("Failed to crawl uncrawled behandelde kamerstukdossiers for %s (%s)", handeling, exc)
