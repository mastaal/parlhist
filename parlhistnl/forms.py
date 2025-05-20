"""
parlhist/parlhistnl/forms.py

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
"""

import datetime

from django import forms

current_year = datetime.date.today().year


class StaatsbladCrawlYearForm(forms.Form):
    jaargang = forms.IntegerField(min_value=1995, max_value=current_year)
