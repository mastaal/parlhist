"""
parlhist/parlhistnl/crawler/kamerdossier.py

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-FileCopyrightText: 2023-2024 Martijn Staal <parlhist [at] martijn-staal.nl>
SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
SPDX-License-Identifier: EUPL-1.2
"""

import logging

from parlhistnl.models import Kamerstuk
from parlhistnl.crawler.utils import CrawlerException
from parlhistnl.crawler.kamerstuk import crawl_all_kamerstukken_within_koop_sru_query

logger = logging.getLogger(__name__)


def crawl_kamerstukdossier(
    dossiernummer: str, update=False, ignore_failure=False
) -> list[Kamerstuk]:
    """Crawl all kamerstukken in a kamerstukdossier"""

    logger.info("Crawling kamerstukdossier %s", dossiernummer)

    query = f"(c.product-area=officielepublicaties AND w.dossiernummer=={dossiernummer} AND w.publicatienaam=Kamerstuk)"
    logger.debug("Generated query %s", query)

    try:
        kamerstukken = crawl_all_kamerstukken_within_koop_sru_query(
            query, update=update
        )
    except Exception as exc:
        logger.fatal("Got exception %s", exc)
        if ignore_failure:
            pass
        else:
            raise CrawlerException from exc

    return kamerstukken
