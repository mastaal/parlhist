"""
parlhist/parlhistnl/tests/test_inwerkingtredingsbepalingen.py

Tests for parlhistnl/utils/inwerkingtredingsbepalingen.py

Copyright 2025 Martijn Staal <parlhist [at] martijn-staal.nl>

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-License-Identifier: EUPL-1.2
"""

import datetime

from django.test import TestCase

from parlhistnl.utils.inwerkingtredingsbepalingen import (
    find_inwerkingtredingsbepaling,
    InwerkingtredingsbepalingType,
    find_inwerkingtredingskb_via_lido,
)
from parlhistnl.models import Staatsblad
from parlhistnl.crawler.staatsblad import crawl_staatsblad


class FindInwerkingtredingsbepalingenTestCase(TestCase):
    """Tests for the automatic recognition and labeling of inwerkingtredingsbepalingen"""

    def test_stb_1995_24(self):
        # This act does not have an inwerkingtredingsbepaling but should have
        stb: Staatsblad = crawl_staatsblad(
            1995,
            24,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-1995-24.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertEqual(len(res["labeled_matches"]), 0)
        self.assertEqual(res["label"], InwerkingtredingsbepalingType.ONBEKEND)

    def test_stb_1995_158(self):
        stb: Staatsblad = crawl_staatsblad(
            1995,
            158,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-1995-158.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(res["label"], InwerkingtredingsbepalingType.GEEN_DELEGATIE)

    def test_stb_1995_662(self):
        stb: Staatsblad = crawl_staatsblad(
            1995,
            662,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-1995-662.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(res["label"], InwerkingtredingsbepalingType.GEEN_DELEGATIE)

    def test_stb_1995_200(self):
        stb: Staatsblad = crawl_staatsblad(
            1995,
            200,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-1995-200.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(
            res["label"], InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        )

    def test_stb_1995_642(self):
        stb: Staatsblad = crawl_staatsblad(
            1995,
            642,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-1995-642.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(res["label"], InwerkingtredingsbepalingType.GEEN_DELEGATIE)

    def test_stb_1995_152(self):
        stb: Staatsblad = crawl_staatsblad(
            1995,
            152,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-1995-152.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(res["label"], InwerkingtredingsbepalingType.GEEN_DELEGATIE)

    def test_stb_1995_554(self):
        stb: Staatsblad = crawl_staatsblad(
            1995,
            554,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-1995-554.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(
            res["label"], InwerkingtredingsbepalingType.DELEGATIE_ZONDER_DIFFERENTIATIE
        )

    def test_stb_1995_319(self):
        stb: Staatsblad = crawl_staatsblad(
            1995,
            319,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-1995-319.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(
            res["label"], InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        )

    def test_stb_2024_193(self):
        stb: Staatsblad = crawl_staatsblad(
            2024,
            193,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2024-193.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(
            res["label"], InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        )

    def test_stb_2022_345(self):
        stb: Staatsblad = crawl_staatsblad(
            2022,
            345,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2022-345.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(
            res["label"], InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        )

    def test_stb_2022_304(self):
        stb: Staatsblad = crawl_staatsblad(
            2022,
            304,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2022-304.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(
            res["label"], InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        )

    def test_stb_2022_330(self):
        stb: Staatsblad = crawl_staatsblad(
            2022,
            330,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2022-330.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(
            res["label"], InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        )

    def test_stb_2022_532(self):
        stb: Staatsblad = crawl_staatsblad(
            2022,
            532,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2022-532.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(res["label"], InwerkingtredingsbepalingType.GEEN_DELEGATIE)

    def test_stb_2025_21(self):
        stb: Staatsblad = crawl_staatsblad(
            2025,
            21,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2025-21.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(res["label"], InwerkingtredingsbepalingType.GEEN_DELEGATIE)

    def test_stb_2017_231(self):
        stb: Staatsblad = crawl_staatsblad(
            2017,
            231,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2017-231.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(
            res["label"], InwerkingtredingsbepalingType.DELEGATIE_EN_DIFFERENTIATIE
        )

    def test_stb_2017_116(self):
        stb: Staatsblad = crawl_staatsblad(
            2017,
            116,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2017-116.html",
        )
        res = find_inwerkingtredingsbepaling(stb)

        print(res["labeled_matches"])
        self.assertGreater(len(res["labeled_matches"]), 0)
        self.assertEqual(res["label"], InwerkingtredingsbepalingType.GEEN_DELEGATIE)


class FindInwerkingtredingsKbViaLidoTestCase(TestCase):

    def test_stb_2024_193_findiwtrkb(self):
        stb: Staatsblad = crawl_staatsblad(
            2024,
            193,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2024-193.html",
        )

        stb_2024_197 = crawl_staatsblad(
            2024,
            197,
            preferred_url="https://zoek.officielebekendmakingen.nl/stb-2024-197.html",
        )

        inwerkingtredingkbs, inwerkingtredingsdata, _, _ = (
            find_inwerkingtredingskb_via_lido(stb)
        )

        expected_kbs = {stb_2024_197}
        expected_dates = {datetime.date(2024, 7, 1), datetime.date(2025, 1, 1)}
