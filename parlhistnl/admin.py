"""
parlhist/parlhistnl/admin.py

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
SPDX-FileCopyrightText: 2023, 2025 Martijn Staal <parlhist [at] martijn-staal.nl>
"""

from django.contrib import admin

from .models import Handeling, Kamerstuk, KamerstukDossier, Staatsblad

admin.site.register(Handeling)
admin.site.register(Kamerstuk)
admin.site.register(KamerstukDossier)
admin.site.register(Staatsblad)
