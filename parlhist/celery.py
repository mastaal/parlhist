"""
    parlhist/parlhist/celery.py

    Celery configuration
    Based on: https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
    SPDX-License-Identifier: EUPL-1.2
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parlhist.settings")

app = Celery("parlhist")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
