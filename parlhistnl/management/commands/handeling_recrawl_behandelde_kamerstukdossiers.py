"""
    parlhist/parlhistnl/management/commands/handeling_recrawl_behandelde_kamerstukdossiers.py

    Crawl one Vergadering and all its subitems

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging
from typing import Any

from django.core.management import BaseCommand
import django_rq

from parlhistnl.crawler.handeling import recrawl_behandelde_kamerstukdossiers
from parlhistnl.models import Handeling

logger = logging.getLogger(__name__)


def job_wrapper_recrawl_behandelde_kamerstukdossiers(handeling: Handeling) -> None:
    """Recrawl and log information, simple wrapper function for easy job enqueuing"""

    logger.info("Crawling behandelde kamerstukken for %s", handeling)
    try:
        kamerstukken = recrawl_behandelde_kamerstukdossiers(handeling)
    except Exception as exc:
        logger.error(
            "Received exception %s while recrawling kamerstukdossiers for %s",
            exc,
            handeling,
        )

    logger.info("Successfully created %s", kamerstukken)


class Command(BaseCommand):
    """Crawl one Vergadering and all its subitems"""

    help = "Crawl one Vergadering and all its subitems"

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Crawl one Vergadering and all its subitems"""

        handelingen = Handeling.objects.all()

        ENQUEUE_JOBS = False

        for handeling in handelingen:
            if ENQUEUE_JOBS:
                django_rq.enqueue(
                    job_wrapper_recrawl_behandelde_kamerstukdossiers, handeling
                )
            else:
                job_wrapper_recrawl_behandelde_kamerstukdossiers(handeling)
