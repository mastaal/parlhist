"""
parlhist/parlhistnl/models.py

Available under the EUPL-1.2, or, at your option, any later version.

SPDX-FileCopyrightText: 2023-2025 Martijn Staal <parlhist [at] martijn-staal.nl>
SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
SPDX-License-Identifier: EUPL-1.2
"""

import datetime
import logging
import re

from bs4 import BeautifulSoup
from django.db import models

logger = logging.getLogger(__name__)
stb_id_pattern = re.compile(r"^stb-\d{4}-\d+(-n\d+)?$")


class Handeling(models.Model):
    """Model for the Handeling of a (part of a) plenary meeting"""

    identifier = models.CharField(max_length=48, unique=True, null=True, default=None)
    kamer = models.CharField(
        max_length=2,
        choices=[("ek", "Eerste Kamer"), ("tk", "Tweede Kamer")],
        default="tk",
    )
    vergaderdag = models.DateField(default=datetime.date(1800, 1, 1))
    vergaderjaar = models.CharField(max_length=9, default="")

    titel = models.TextField()
    handelingtype = models.CharField(max_length=1024)

    tekst = models.TextField()
    raw_html = models.TextField()
    raw_xml = models.TextField(default="")
    raw_metadata_xml = models.TextField()
    sru_record_xml = models.BinaryField(default=b"")

    behandelde_kamerstukdossiers = models.ManyToManyField(to="KamerstukDossier")
    behandelde_kamerstukken = models.ManyToManyField(to="Kamerstuk")

    preferred_url = models.URLField(default="")

    # Flexible field for storing various data about this Handeling
    data = models.JSONField(default=dict)
    # Currently, this field is used to store recognized but not crawled kamerstukken/kamerstukdossiers:
    # { "uncrawled": { "behandelde_kamerstukken": [ "36160;5", ...], "behandelde_kamerstukdossiers": ["36130", ... ] }}

    toegevoegd_op = models.DateTimeField(auto_now_add=True)
    bijgewerkt_op = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta information for django"""

        indexes = []

        verbose_name_plural = "Handelingen"

    def __str__(self) -> str:
        if self.identifier is not None:
            return self.identifier

        return "Handeling with no identifier"

    def url(self) -> str:
        """Get the url to this Handeling"""
        if self.preferred_url != "":
            return self.preferred_url
        return f"https://zoek.officielebekendmakingen.nl/{self.identifier}.html"


class KamerstukDossier(models.Model):
    """Model for a kamerstukdossier"""

    dossiernummer = models.CharField(max_length=64)
    dossiertitel = models.TextField()

    toegevoegd_op = models.DateTimeField(auto_now_add=True)
    bijgewerkt_op = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta information for django"""

        indexes = [
            models.Index(fields=["dossiernummer"]),
        ]

        verbose_name_plural = "KamerstukDossiers"

    def __str__(self) -> str:
        return f"{self.dossiernummer}: {self.dossiertitel}"


class Kamerstuk(models.Model):
    """Model for a single kamerstuk"""

    vergaderjaar = models.CharField(max_length=8)
    hoofddossier = models.ForeignKey(KamerstukDossier, on_delete=models.CASCADE)

    # TODO: Support multiple dossiers
    # dossier = models.ManyToManyField(KamerstukDossier)

    # Primary ondernummer
    # Must also be able to be characters for EK
    ondernummer = models.CharField(max_length=64)
    kamer = models.CharField(
        max_length=2,
        choices=[("ek", "Eerste Kamer"), ("tk", "Tweede Kamer")],
        default="tk",
    )

    class KamerstukType(models.TextChoices):
        """Specialized enum for kamerstuk types"""

        KONINKLIJKE_BOODSCHAP = "Koninklijke boodschap"
        GELEIDENDE_BRIEF = "Geleidende brief"
        WETSVOORSTEL = "Voorstel van wet"
        MEMORIE_VAN_TOELICHTING = "Memorie van toelichting"
        ADVIES_RVS = "Advies Raad van State"
        VOORLICHTING_RVS = (
            "Voorlichting van de Afdeling advisering van de Raad van State"
        )
        VERSLAG = "Verslag"
        NOTA_NA_VERSLAG = "Nota naar aanleiding van het verslag"
        NOTA_VAN_WIJZIGING = "Nota van wijziging"
        NOTA_VAN_VERBETERING = "Nota van verbetering"
        MEMORIE_VAN_ANTWOORD = "Memorie van antwoord"
        AMENDEMENT = "Amendement"
        MOTIE = "Motie"
        BRIEF = "Brief"
        JAARVERSLAG = "Jaarverslag"
        LIJST_VAN_VRAGEN_EN_ANTWOORDEN = "Lijst van vragen en antwoorden"
        ONBEKEND = "Onbekend"

    kamerstuktype = models.CharField(
        max_length=256, choices=KamerstukType.choices, default=KamerstukType.ONBEKEND
    )
    documenttitel = models.TextField()
    indiener = models.TextField()

    tekst = models.TextField()
    raw_html = models.TextField()
    raw_metadata_xml = models.TextField()

    documentdatum = models.DateField(
        help_text="Datum van het document volgens DCTERMS.issued",
        default=datetime.date(1800, 1, 1),
    )
    toegevoegd_op = models.DateTimeField(auto_now_add=True)
    bijgewerkt_op = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta information for django"""

        indexes = [
            models.Index(fields=["vergaderjaar"]),
            models.Index(fields=["kamerstuktype"]),
            models.Index(fields=["hoofddossier", "ondernummer"]),
            models.Index(fields=["hoofddossier", "ondernummer", "kamer"]),
        ]

        verbose_name_plural = "Kamerstukken"

    # TODO Add support for attachments to kamerstukken

    def __str__(self) -> str:
        return f"Kamerstuk {self.hoofddossier.dossiernummer}-{self.ondernummer} {self.kamerstuktype}: {self.documenttitel} ({self.documentdatum})"

    def url(self) -> str:
        """Get the URL to this Kamerstuk"""
        return f"https://zoek.officielebekendmakingen.nl/kst-{self.hoofddossier.dossiernummer}-{self.ondernummer}.html"


class StaatsbladManager(models.Manager):
    """Custom manager for Staatsblad model"""

    def get_staatsblad_from_stbid(self, stbid: str):
        """Get a Staatsblad object using an id that is in the form of stb-2024-193"""

        if stb_id_pattern.match(stbid) is not None:
            try:
                _, jaargang_str, nummer_str = stbid.split("-")
                jaargang = int(jaargang_str)
                nummer = int(nummer_str)

                stb = self.get(jaargang=jaargang, nummer=nummer, versienummer="")
            except ValueError:
                logger.debug("Value error, expecting verbeterblad")
                _, jaargang_str, nummer_str, versie_str = stbid.split("-")
                stb = self.get(jaargang=int(jaargang_str), nummer=int(nummer_str), versienummer=versie_str)

            return stb


class Staatsblad(models.Model):
    """Model for a publication in the Staatsblad"""

    jaargang = models.IntegerField()
    nummer = models.IntegerField()
    versienummer = models.CharField(max_length=16, default="")

    behandelde_dossiers = models.ManyToManyField(KamerstukDossier)

    titel = models.TextField()
    tekst = models.TextField()
    raw_html = models.TextField()
    raw_xml = models.TextField()
    raw_metadata_xml = models.TextField()
    metadata_json = models.JSONField()

    publicatiedatum = models.DateField()
    ondertekendatum = models.DateField()

    toegevoegd_op = models.DateTimeField(auto_now_add=True)
    bijgewerkt_op = models.DateTimeField(auto_now=True)

    class StaatsbladType(models.TextChoices):
        """Specialized enum for Staatsblad types"""

        WET = "Wet"
        RIJKSWET = "Rijkswet"
        AMVB = "AMvB"
        RIJKSAMVB = "RijksAMvB"
        VERBETERBLAD = "Verbeterblad"
        ONBEKEND = "Onbekend"
        KKB = "Klein Koninklijk Besluit"
        INTEGRALE_TEKSTPLAATSING = "Integrale tekstplaatsing"

    staatsblad_type = models.CharField(
        max_length=256, choices=StaatsbladType.choices, default=StaatsbladType.ONBEKEND
    )

    preferred_url = models.URLField(null=True)

    objects = StaatsbladManager()

    class Meta:
        """Meta information for django"""

        indexes = [
            models.Index(fields=["jaargang", "nummer"]),
        ]

        verbose_name_plural = "Staatsbladen"

    def __str__(self) -> str:
        if self.versienummer == "":
            return f"Staatsblad {self.jaargang}-{self.nummer} {self.staatsblad_type}: {self.titel} ({self.publicatiedatum})"
        return f"Staatsblad {self.jaargang}-{self.nummer}-{self.versienummer} {self.staatsblad_type}: {self.titel} ({self.publicatiedatum})"

    def __title_based_staatsblad_property_check_all(
        self, check_strings: list[str]
    ) -> bool:
        """
        Base method to create title-based identification methods. The title must mention
        all of the given check strings.

        The titel is normalized first.
        """

        normalized_title = self.titel.lower()

        return all([x in normalized_title for x in check_strings])

    def __title_based_staatsblad_property_check_any(
        self, check_strings: list[str]
    ) -> bool:
        """
        Base method to create title-based identification methods. The title must mention
        any of the given check strings.

        The titel is normalized first.
        """

        normalized_title = self.titel.lower()

        return any([x in normalized_title for x in check_strings])

    @property
    def is_wet(self) -> bool:
        """Is this a StaatsbladType.WET or StaatsbladType.RIJKSWET?"""

        if (
            self.staatsblad_type == Staatsblad.StaatsbladType.WET
            or self.staatsblad_type == Staatsblad.StaatsbladType.RIJKSWET
        ):
            return True

        return False

    @property
    def is_goedkeuringswet_verdrag(self) -> bool:
        """Returns true if this Staatsblad probably contains a goedkeuringswet for a verdrag"""

        check_strings = ["trb", "goedkeuring"]

        return self.is_wet and self.__title_based_staatsblad_property_check_all(
            check_strings
        )

    @property
    def is_begrotingswet(self) -> bool:
        """Returns true if this Staatsblad probably contains a begrotingswet"""

        check_strings = ["begrotingsstaat", "begrotingsstaten"]

        return self.is_wet and self.__title_based_staatsblad_property_check_any(
            check_strings
        )

    @property
    def is_slotwet(self) -> bool:
        """Returns true if this Staatsblad probably contains a slotwet"""

        check_strings = ["slotwet"]

        return self.is_wet and self.__title_based_staatsblad_property_check_all(
            check_strings
        )

    @property
    def is_vaststelling_grond_grondwetswijziging(self) -> bool:
        """Returns true if this Staatsblad probably contains a wet houdende verklaring dat er grond bestaat een voorstel in overweging te nemen tot verandering in de Grondwet"""

        check_strings = [
            "houdende verklaring dat er grond bestaat een voorstel in overweging te nemen tot verandering in de grondwet"
        ]

        return self.is_wet and self.__title_based_staatsblad_property_check_all(
            check_strings
        )

    @property
    def stbid(self) -> str:
        """Returns the stb-id in the form: stb-{jaargang}-{nummer}"""
        if self.versienummer == "":
            return f"stb-{self.jaargang}-{self.nummer}"

        return f"stb-{self.jaargang}-{self.nummer}-{self.versienummer}"

    def get_articles_list(self, include_article_names=False) -> list[str]:
        """Returns a list with the text of all seperate articles as found using the raw html"""

        soup = BeautifulSoup(self.raw_html, "html.parser")
        html_header_re = re.compile(r"h\d")

        artikel_selector = "div.artikel"

        if include_article_names:
            return [
                artikel_html.get_text()
                for artikel_html in soup.select(artikel_selector)
            ]
        else:
            artikelen_html = soup.select(artikel_selector)
            for artikel_html in artikelen_html:
                # Remove all the headers first
                for header in artikel_html.find_all(html_header_re):
                    header.extract()

            return [artikel_html.get_text().strip() for artikel_html in artikelen_html]
