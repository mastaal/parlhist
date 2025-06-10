"""
    parlhist/parlhistnl/crawler/utils.py

    Copyright 2023, 2024, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import hashlib
import logging
import pathlib
import pickle
import time
import xml.etree.ElementTree as ET

from typing import Literal
from xml.etree.ElementTree import Element

import requests

from django.conf import settings

logger = logging.getLogger(__name__)
XML_NAMESPACES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dcterms": "http://purl.org/dc/terms/",
    "psi": "http://psi.rechtspraak.nl/",
    "rs": "http://www.rechtspraak.nl/schema/rechtspraak-1.0",
    "ecli": "https://e-justice.europa.eu/ecli",
    "overheidwetgeving": "http://standaarden.overheid.nl/wetgeving/",
    "sru": "http://docs.oasis-open.org/ns/search-ws/sruResponse",
    "gzd": "http://standaarden.overheid.nl/sru",
    "c": "http://standaarden.overheid.nl/collectie/",
}


class CrawlerException(Exception):
    """For when something goes wrong during crawling"""


def __get_memoized_path(url: str) -> str:
    """Get the full memoized path given a url"""
    fn = hashlib.sha1(url.encode("utf-8")).hexdigest()
    base_path = pathlib.Path(
        f"{settings.PARLHIST_CRAWLER_MEMOIZE_PATH}/{fn[0]}/{fn[1]}"
    )
    base_path.mkdir(mode=0o755, parents=True, exist_ok=True)

    full_path = f"{base_path}/{fn}"

    return full_path


def __check_response_status_code(response: requests.Response) -> None:
    """Check the status code of a response; if it is not 200, throw an CrawlerException"""

    if response.status_code != 200:
        logger.error(
            "Received not-OK status code from page get %s", response.status_code
        )
        raise CrawlerException(
            f"Received not-OK status code from page get {response.status_code}"
        )


# TODO: Would be nice to also pass custom parameters, cookies and timeout values
def get_url_or_error(
    url: str, memoize=settings.PARLHIST_CRAWLER_DEFAULT_USE_MEMOIZATION
) -> requests.Response:
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
        logger.debug(
            "Actual request was sent, sleeping to prevent service disruption at receiver end"
        )
        time.sleep(0.25)
    except requests.exceptions.ReadTimeout as exc:
        raise CrawlerException from exc

    if response.encoding != response.apparent_encoding:
        logger.info(
            "Encoding is not the same as apparent encoding, adjusting encoding %s %s",
            response.encoding,
            response.apparent_encoding,
        )
        response.encoding = response.apparent_encoding

    __check_response_status_code(response)

    if memoize:
        full_path = __get_memoized_path(url)

        logger.debug("Memoizing request to %s", full_path)

        with open(full_path, "wb") as pickle_file:
            pickle.dump(response, pickle_file, pickle.HIGHEST_PROTOCOL)

    return response


def koop_sru_api_request(
    query: str, start_record: int, maximum_records: int
) -> Element:
    """Query the KOOP SRU API, return the complete response xml."""
    api_url = "https://repository.overheid.nl/sru"

    resp = requests.get(
        api_url,
        params={
            "httpAccept": "application/xml",
            "startRecord": start_record,
            "maximumRecords": maximum_records,
            "query": query,
        },
        timeout=25,
    )

    if resp.status_code != 200:
        logger.error(
            "Non-200 status code while retrieving SRU API with query %s", query
        )
        raise CrawlerException(
            f"Non-200 status code while retrieving SRU API with query {query}"
        )

    xml: Element = ET.fromstring(resp.text)

    return xml


def koop_sru_api_request_all(query: str) -> list[Element]:
    """Query the KOOP SRU API. Returns all records for the query, even if this requires multiple requests.

    See https://data.overheid.nl/sites/default/files/dataset/d0cca537-44ea-48cf-9880-fa21e1a7058f/resources/Handleiding%2BSRU%2B2.0.pdf
    for more information about this API.
    """

    start_record = 0
    maximum_records = 1000
    xml = koop_sru_api_request(query, start_record, maximum_records)
    records = xml.findall("sru:records/sru:record", XML_NAMESPACES)

    number_of_records = int(xml.find("sru:numberOfRecords", XML_NAMESPACES).text)

    while len(records) < number_of_records:
        # We need another request to get all the records!
        start_record = start_record + maximum_records
        xml = koop_sru_api_request(query, start_record, maximum_records)
        records += xml.findall("sru:records/sru:record", XML_NAMESPACES)

    return records


def __retrieve_xml_element_or_fail(xml: ET.Element, path: str) -> ET.Element:
    """Search the xml for path and retrieve this element, or raise a CrawlerException if no element could be found."""
    search_result_xml = xml.find(path=path, namespaces=XML_NAMESPACES)
    if search_result_xml is None:
        raise CrawlerException(f"Could not find {path} in {xml}")

    return search_result_xml


def retrieve_xml_element_text_or_fail(xml: ET.Element, path: str) -> str:
    """Search xml for path and retrieve its text, or raise a CrawlerException if no text could be found."""

    search_result_xml = __retrieve_xml_element_or_fail(xml, path)

    search_result_text = search_result_xml.text
    if search_result_text is None:
        raise CrawlerException(f"Search result {search_result_xml} for {path} in {xml} has no inner text")

    return search_result_text


def retrieve_xml_element_keyed_value_or_fail(xml: ET.Element, path: str, key: str) -> str:
    """Search xml for path, retrieve the value given by key, or raise a CrawlerException if no value could be found."""

    search_result_xml = __retrieve_xml_element_or_fail(xml, path)

    search_result_value = search_result_xml.get(key)
    if search_result_value is None:
        raise CrawlerException(f"Could not find {key} in the retrieved {search_result_xml} in {xml} using {path}")

    return search_result_value


def shorten_kamer(creator: str) -> Literal["ek", "tk"]:
    """Shorten Tweede Kamer der Staten-Generaal or Eerste Kamer der Staten-Generaal to tk or ek respectively."""
    if creator == "Tweede Kamer der Staten-Generaal":
        return "tk"

    if creator == "Eerste Kamer der Staten-Generaal":
        return "ek"

    raise CrawlerException(f"Could not find the appropriate abbreviation for {creator}")
