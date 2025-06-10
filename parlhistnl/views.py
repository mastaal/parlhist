"""
parlhist/parlhistnl/views.py

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import logging

from django.core.management import call_command
from django.shortcuts import render

from parlhistnl.forms import StaatsbladCrawlYearForm
from parlhistnl.models import Handeling, Kamerstuk, Staatsblad
from parlhistnl.crawler.staatsblad import crawl_all_staatsblad_publicaties_in_year

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):
    """Render the main page, with information and the url to get a report"""

    # Generate some status information to show
    status_information = [
        ("Aantal Kamerstukken", Kamerstuk.objects.all().count()),
        ("Aantal Handelingen", Handeling.objects.all().count()),
        ("Aantal Staatsblad-publicaties", Staatsblad.objects.all().count()),
    ]

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = StaatsbladCrawlYearForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            logger.info(form.cleaned_data)
            # TODO: Use this to create some nice interface to show current progress
            # TODO: Even starting this creates quite a long call, so this should be a task itself
            async_stb_crawl_results = crawl_all_staatsblad_publicaties_in_year(
                form.cleaned_data["jaargang"], update=False, queue_tasks=True
            )
    # if a GET (or any other method) we'll create a blank form
    else:
        form = StaatsbladCrawlYearForm()

    return render(
        request,
        "parlhistnl/index.html",
        {"form": form, "status_information": status_information},
    )
