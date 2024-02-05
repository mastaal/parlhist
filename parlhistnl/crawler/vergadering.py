"""
    parlhist/parlhistnl/crawler/vergadering.py

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import datetime
import logging
import time
import xml.etree.ElementTree as ET

from parlhistnl.models import Vergadering
from parlhistnl.crawler.utils import CrawlerException, get_url_or_error
from parlhistnl.crawler.handeling import crawl_vergadering_subitem

logger = logging.getLogger(__name__)


def __get_vergaderdatum(xml: ET.Element) -> datetime.date:
    """Get the vergaderdatum from a parsed metadata xml"""

    vergaderdatumstr = xml.findall("metadata[@name='OVERHEIDop.datumVergadering']")[0].get("content")

    return datetime.datetime.strptime(vergaderdatumstr, "%Y-%m-%d").date()


def crawl_vergadering(vergaderjaar: str, nummer: int, kamer="tk") -> Vergadering:
    """Crawl a vergadering and all its sub items"""

    item: int = 1

    base_url = f"https://zoek.officielebekendmakingen.nl/h-{kamer}-{vergaderjaar}-{nummer}-{item}"
    # html_url = f"{base_url}.html"
    meta_url = f"{base_url}/metadata.xml"

    # First, check if it could actually exist
    # Why is/was this request there?
    # try:
    #     text_response = __get_url_or_error(html_url)
    # except CrawlerException as exc:
    #     logger.fatal("This vergadering seems to not exist")
    #     raise CrawlerException("This vergadering seems to not exist") from exc

    try:
        meta_response = get_url_or_error(meta_url)
    except CrawlerException as exc:
        logger.fatal("This vergadering seems to not exist")
        raise CrawlerException("This vergadering seems to not exist") from exc

    xml = ET.fromstring(meta_response.text)

    vergaderdatum = __get_vergaderdatum(xml)

    vergadering, created = Vergadering.objects.get_or_create(
        vergaderjaar=vergaderjaar,
        nummer=nummer,
        kamer=kamer,
        vergaderdatum=vergaderdatum
    )

    if created:
        logger.debug("Created new vergadering %s", vergadering)
    else:
        logger.debug("Crawled existing vergadering %s", vergadering)

    error_count = 0

    while error_count < 2:
        try:
            handeling = crawl_vergadering_subitem(vergadering, item)
            logger.debug("Crawled %s", handeling)
        except CrawlerException:
            error_count += 1

        item += 1

    return vergadering
