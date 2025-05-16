"""
parlhist/parlhistnl/management/commands/export_to_opensearch.py

Export parlhist data to an OpenSearch instance

Copyright 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-File-CopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
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

from parlhistnl.models import Staatsblad

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Export parlhist data to an OpenSearch instance"""

    help = "Export parlhist data to an OpenSearch instance"

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments"""
        parser.add_argument(
            "model",
            type=str,
            choices=["Staatsblad"],
            help="Choose which model you want to export to OpenSearch",
        )

    def handle(self, *args: Any, **options: Any) -> str | None:

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

        # We need to create a new index if it doesn't already exist
        if not os_client.indices.exists(index_name):
            logger.info(
                "Index %s does not already exist, creating new index...", index_name
            )
            create_response = os_client.indices.create(index_name)
            # The response for this API endpoint is currently (OS v.3.0) not documented, so just hope
            # that this worked! https://docs.opensearch.org/docs/3.0/api-reference/index-apis/create-index/
            logger.debug(create_response)
        else:
            logger.debug("Index %s already exists", index_name)

        if options["model"] == "Staatsblad":
            staatsbladen = Staatsblad.objects.exclude(
                staatsblad_type=Staatsblad.StaatsbladType.VERBETERBLAD
            )

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
        else:
            logger.error("No valid / known model to export specified")
            self.stderr.write(
                self.style.ERROR("No valid or known model to export specified!")
            )
