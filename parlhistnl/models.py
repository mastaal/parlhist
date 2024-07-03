"""
    parlhist/parlhistnl/models.py

    Copyright 2023, 2024 Martijn Staal <parlhist [at] martijn-staal.nl>

    Available under the EUPL-1.2, or, at your option, any later version.

    SPDX-License-Identifier: EUPL-1.2
"""

import datetime
import logging

from django.db import models

logger = logging.getLogger(__name__)


class Vergadering(models.Model):
    """Model for a plenary meeting"""

    vergaderjaar = models.CharField(max_length=8)
    nummer = models.IntegerField()
    kamer = models.CharField(
        max_length=2,
        choices=[("ek", "Eerste Kamer"), ("tk", "Tweede Kamer")],
        default="tk",
    )

    vergaderdatum = models.DateField(default=datetime.date(year=1800, month=1, day=1))

    toegevoegd_op = models.DateTimeField(auto_now_add=True)
    bijgewerkt_op = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta information for django"""

        indexes = [
            models.Index(fields=["vergaderjaar", "nummer", "kamer"]),
            models.Index(fields=["vergaderjaar", "nummer", "kamer", "vergaderdatum"]),
        ]

    def __str__(self):
        return f"Vergadering h-{self.kamer}-{self.vergaderjaar}-{self.nummer}"


class Handeling(models.Model):
    """Model for the Handeling of a (part of a) plenary meeting"""

    vergadering = models.ForeignKey(to=Vergadering, on_delete=models.CASCADE)
    ondernummer = models.IntegerField()
    titel = models.TextField()
    handelingtype = models.CharField(max_length=1024)

    tekst = models.TextField()
    raw_html = models.TextField()
    raw_metadata_xml = models.TextField()

    behandelde_kamerstukdossiers = models.ManyToManyField(to="KamerstukDossier")
    behandelde_kamerstukken = models.ManyToManyField(to="Kamerstuk")

    # Flexible field for storing various data about this Handeling
    data = models.JSONField(default=dict)
    # Currently, this field is used to stored recognized but not crawled kamerstukken/kamerstukdossiers:
    # { "uncrawled": { "behandelde_kamerstukken": [ "36160;5", ...], "behandelde_kamerstukdossiers": ["36130", ... ] }}

    toegevoegd_op = models.DateTimeField(auto_now_add=True)
    bijgewerkt_op = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta information for django"""

        indexes = [
            models.Index(fields=["vergadering", "ondernummer"]),
        ]

    def __str__(self) -> str:
        return f"h-{self.vergadering.kamer}-{self.vergadering.vergaderjaar}-{self.vergadering.nummer}-{self.ondernummer}"  # pylint: disable=no-member

    def url(self) -> str:
        """Get the url to this Handeling"""
        return f"https://zoek.officielebekendmakingen.nl/h-{self.vergadering.kamer}-{self.vergadering.vergaderjaar}-{self.vergadering.nummer}-{self.ondernummer}.html"  # pylint: disable=no-member


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

    # TODO Add support for attachments to kamerstukken

    def __str__(self) -> str:
        return f"Kamerstuk {self.hoofddossier.dossiernummer}-{self.ondernummer} {self.kamerstuktype}: {self.documenttitel} ({self.documentdatum})"

    def url(self) -> str:
        """Get the URL to this Kamerstuk"""
        return f"https://zoek.officielebekendmakingen.nl/kst-{self.hoofddossier.dossiernummer}-{self.ondernummer}.html"


class Staatsblad(models.Model):
    """Model for a publication in the Staatsblad"""

    jaargang = models.IntegerField()
    nummer = models.IntegerField()

    behandelde_dossiers = models.ManyToManyField(KamerstukDossier)

    titel = models.TextField()
    tekst = models.TextField()
    raw_html = models.TextField()
    raw_metadata_xml = models.TextField()

    publicatiedatum = models.DateField()
    ondertekendatum = models.DateField()

    toegevoegd_op = models.DateTimeField(auto_now_add=True)
    bijgewerkt_op = models.DateTimeField(auto_now=True)

    class StaatsbladType(models.TextChoices):
        """Specialized enum for Staatsblad types"""

        WET = "Wet"
        AMVB = "AMvB"
        VERBETERBLAD = "Verbeterblad"
        ONBEKEND = "Onbekend"

    staatsblad_type = models.CharField(
        max_length=256, choices=StaatsbladType.choices, default=StaatsbladType.ONBEKEND
    )

    class Meta:
        """Meta information for django"""

        indexes = [
            models.Index(fields=["jaargang", "nummer"]),
        ]

    def __str__(self) -> str:
        return f"Staatsblad {self.jaargang}-{self.nummer} {self.staatsblad_type}: {self.titel} ({self.publicatiedatum})"
