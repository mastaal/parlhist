"""
    parlhist/parlhistnl/admin.py

    Copyright 2023, Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

from django.contrib import admin

from .models import Vergadering, Handeling, Kamerstuk, KamerstukDossier

admin.site.register(Vergadering)
admin.site.register(Handeling)
admin.site.register(Kamerstuk)
admin.site.register(KamerstukDossier)
