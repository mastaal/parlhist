"""
    parlhist/parlhist/__init__.py

    Based on: https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
    SPDX-License-Identifier: EUPL-1.2
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
