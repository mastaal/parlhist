"""
    parlhist/parlhistnl/management/commands/export_to_opensearch.py

    Export parlhist data to an OpenSearch instance

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
    SPDX-License-Identifier: EUPL-1.2
"""

import json
import logging
from typing import Any

from django.conf import settings
from django.core import serializers
from django.core.management import BaseCommand
from django.core.management.base import CommandParser
from opensearchpy import OpenSearch, helpers

from parlhistnl.models import Staatsblad, Kamerstuk, KamerstukDossier

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Export parlhist data to an OpenSearch instance"""

    help = "Export parlhist data to an OpenSearch instance"

    def __create_os_index_if_not_exists(self, os_client, index_name: str) -> bool:
        """
        Create a new index in OpenSearch if it does not already exists.

        Returns True if a new index has been created.
        """
        if not os_client.indices.exists(index_name):
            logger.info(
                "Index %s does not already exist, creating new index...", index_name
            )
            create_response = os_client.indices.create(index_name)
            # The response for this API endpoint is currently (OS v.3.0) not documented, so just hope
            # that this worked! https://docs.opensearch.org/docs/3.0/api-reference/index-apis/create-index/
            logger.debug(create_response)
            return True
        else:
            logger.debug("Index %s already exists", index_name)
            return False

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments"""
        parser.add_argument(
            "model",
            type=str,
            choices=["Staatsblad", "Kamerstuk"],
            help="Choose which model you want to export to OpenSearch",
        )

    def handle(self, *args: Any, **options: Any) -> str | None:

        if not settings.PARLHIST_OPENSEARCH_ENABLED:
            self.stderr.write(
                self.style.ERROR("OpenSearch is not enabled.")
            )

            return

        index_name = f"parlhist-{options['model']}".lower()

        os_client = OpenSearch(
            hosts=settings.PARLHIST_OPENSEARCH_HOSTS,
            http_auth=settings.PARLHIST_OPENSEARCH_HTTP_AUTH,
            use_ssl=True,
            verify_certs=settings.PARLHIST_OPENSEARCH_VERIFY_CERTS,
        )

        client_info = os_client.info()
        print(
            f"Welcome to {client_info['version']['distribution']} {client_info['version']['number']}!"
        )

        if options["model"] == "Staatsblad":
            self.__create_os_index_if_not_exists(os_client, index_name)

            staatsbladen = Staatsblad.objects.all()

            staatsbladen_serialized = json.loads(
                serializers.serialize("json", staatsbladen)
            )

            staatsbladen_os = []
            # We need to do some reformatting into a way that OpenSearch will like
            for stb in staatsbladen_serialized:
                stb_os = stb["fields"]
                stb_os["_id"] = f"stb-{stb_os['jaargang']}-{stb_os['nummer']}"
                stb_os["_index"] = index_name
                del stb_os["raw_metadata_xml"]
                staatsbladen_os.append(stb_os)

            helpers.bulk(os_client, staatsbladen_os, max_retries=3)
        elif options["model"] == "Kamerstuk":
            self.__create_os_index_if_not_exists(os_client, index_name)

            kamerstukken = Kamerstuk.objects.all()

            kamerstukken_serialized = json.loads(
                serializers.serialize("json", kamerstukken)
            )

            kamerstukken_os = []
            for kst in kamerstukken_serialized:
                kst_os = kst["fields"]
                hoofddossier = KamerstukDossier.objects.get(id=kst["fields"]["hoofddossier"])
                del kst_os["hoofddossier"]
                kst_os["hoofddossier_nummer"] = hoofddossier.dossiernummer
                kst_os["hoofddossier_titel"] = hoofddossier.dossiertitel
                kst_os["_index"] = index_name
                kst_os["_id"] = f"kst-{hoofddossier.dossiernummer}-{kst_os['ondernummer']}"
                kamerstukken_os.append(kst_os)

            helpers.bulk(os_client, kamerstukken_os, max_retries=3)
        else:
            logger.error("No valid / known model to export specified")
            self.stderr.write(
                self.style.ERROR("No valid or known model to export specified!")
            )
