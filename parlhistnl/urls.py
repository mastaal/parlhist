"""
parlhist/parlhistnl/urls.py

Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
"""

from django.urls import path

from . import views

urlpatterns = [path("", views.index, name="parlhistnl-index")]
