# Experiment amendementen delegatiebepalingen

Dit document vormt de digitale bijlage van het artikel: [TODO artikel toevoegen wanneer deze is gepubliceerd]. Wij beschrijven in dit document hoe je het geautomatiseerde gedeelte van ons empirische onderzoek kan reproduceren.

## Vereisten
Basiskennis van Linux en Python worden verondersteld in deze bijlage.

Het experiment is gedraaid op Ubuntu 22.04 LTS, met Python 3.10.12 en Django 5.1.6. Als database werd een PostgreSQL (versie 14.17) database gebruikt.

Om het experiment te reproduceren wordt uitgegaan van een recente Linux-distributie met PostgreSQL als database. Op andere besturingssystemen en met andere databases zou het experiment ook te reproduceren moeten zijn; maar dit is niet getest.

## Stap 1: installeer parlhist
Om te beginnen, installeer parlhist. Volg hiervoor [de instructies in de README](/README.md).

Zorg ook dat je je database initieert door de Django migraties te draaien (`$ ./manage.py migrate`)

## Stap 2: laadt de Kamerstukken in parlhist
Wanneer je parlhist hebt geïnstalleerd is de volgende stap om de Kamerstukken uit de onderzoeksperiode te downloaden.

Dit kan gedaan worden door gebruik te maken van het hulp-script `initialize_database_kamerstukken.sh`. Zorg dat je eerst op de juiste manier je Python-environment hebt geladen.
```bash
$ ./initialize_database_kamerstukken.sh
```

> [!WARNING]
> Het downloaden van al deze Kamerstukken duurt lang. Dit komt deels omdat parlhist een ingebouwde vertraging heeft bij het downloaden van gegevens om de API van KOOP niet te veel te belasten.

## Stap 3
Nu alle gegevens geladen zijn, is het mogelijk om het experiment te draaien. Het script voor dit experiment is te vinden in [parlhistnl/management/commands/experiment_amendementen_delegatiebepalingen.py](/parlhistnl/management/commands/experiment_amendementen_delegatiebepalingen.py). Neem vooral een kijkje als je benieuwd bent hoe het precies in elkaar zit.

Het experiment kan je op de volgende manier uitvoeren:
```
$ ./manage.py experiment_amendementen_delegatiebepalingen
```

De resultaten van het experiment worden opgeslagen in een aantal bestanden. In de twee CSV bestanden (eentje inclusief de integrale tekst van het amendement, eentje met alleen metagegevens) zijn alle amendementen te vinden die ten minste één match hebben op een variatie op het eerste zinsdeel. Wat voor matches er gevonden zijn in een amendement, is te lezen in de kolom `label`. Aan de hand van deze CSV bestanden kan je vervolgens de handmatige analyse uitvoeren die wij hebben beschreven in ons artikel.