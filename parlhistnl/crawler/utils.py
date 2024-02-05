"""
    parlhist/parlhistnl/crawler/utils.py

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import hashlib
import logging
import pathlib
import pickle
import time

import requests

from django.conf import settings

logger = logging.getLogger(__name__)


class CrawlerException(Exception):
    """For when something goes wrong during crawling"""


def __get_memoized_path(url: str) -> str:
    """Get the full memoized path given a url"""
    fn = hashlib.sha1(url.encode("utf-8")).hexdigest()
    base_path = pathlib.Path(f"{settings.PARLHIST_CRAWLER_MEMOIZE_PATH}/{fn[0]}/{fn[1]}")
    base_path.mkdir(mode=0o755, parents=True, exist_ok=True)

    full_path = f"{base_path}/{fn}"

    return full_path


def __check_response_status_code(response: requests.Response) -> None:
    """Check the status code of a response; if it is not 200, throw an CrawlerException"""

    if response.status_code != 200:
        logger.error("Received not-OK status code from page get %s", response.status_code)
        raise CrawlerException(f"Received not-OK status code from page get {response.status_code}")


def get_url_or_error(url: str, memoize=True) -> requests.Response:
    """Try to get a page, or throw a CrawlerException if it fails

    By default, it memoizes the requests in order to lower issues at the receiver end, but to
    be able to still easily change behaviour on our side.
    Also fixes encoding
    """

    if memoize:
        logger.debug("Checking if memoized version exists for %s", url)
        # First try if a memoized version of this request exists
        full_path = __get_memoized_path(url)
        if pathlib.Path(full_path).exists():
            logger.debug("Memoized request exists, returning that instead")
            # Recover memoized request
            with open(full_path, "rb") as pickle_file:
                response = pickle.load(pickle_file)
                __check_response_status_code(response)
                return response
        else:
            logger.debug("No memoized version exists, hitting server")

    try:
        response = requests.get(url, timeout=30)
        logger.debug("Actual request was sent, sleeping to prevent service disruption at receiver end")
        time.sleep(0.25)
    except requests.exceptions.ReadTimeout as exc:
        raise CrawlerException from exc

    if response.encoding != response.apparent_encoding:
        logger.info("Encoding is not the same as apparent encoding, adjusting encoding %s %s", response.encoding, response.apparent_encoding)
        response.encoding = response.apparent_encoding

    if memoize:
        full_path = __get_memoized_path(url)

        logger.debug("Memoizing request to %s", full_path)

        with open(full_path, "wb") as pickle_file:
            pickle.dump(response, pickle_file, pickle.HIGHEST_PROTOCOL)

    __check_response_status_code(response)

    return response
