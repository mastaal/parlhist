"""
    parlhist/parlhistnl/management/commands/handeling_recrawl_behandelde_kamerstukken.py

    Crawl one Vergadering and all its subitems

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import logging
from typing import Any

from django.core.management import BaseCommand

import django_rq

from parlhistnl.crawler.handeling import recrawl_behandelde_kamerstukken
from parlhistnl.models import Handeling, Kamerstuk

logger = logging.getLogger(__name__)


def job_wrapper_recrawl_behandelde_stukken(handeling: Handeling) -> None:
    """Recrawl and log information, simple wrapper function for easy job enqueueing"""
    logger.info("Crawling behandelde kamerstukken for %s", handeling)
    kamerstukken: list[Kamerstuk] = recrawl_behandelde_kamerstukken(handeling)

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
                django_rq.enqueue(job_wrapper_recrawl_behandelde_stukken, handeling)
            else:
                job_wrapper_recrawl_behandelde_stukken(handeling)
