#!/bin/bash

# SPDX-FileCopyrightText: 2024 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
#
# SPDX-License-Identifier: EUPL-1.2

source ./venv/bin/activate
./manage.py migrate

./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20222023
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20212022
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20202021
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20192020
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20182019
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20172018
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20162017
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20152016
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20142015
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20132014
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20122013
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer ek 20112012

./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20222023
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20212022
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20202021
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20192020
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20182019
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20172018
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20162017
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20152016
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20142015
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20132014
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20122013
./manage.py vergaderdag_crawl_full_vergaderjaar --kamer tk 20112012

./manage.py handeling_crawl_uncrawled_behandelde_kamerstukdossiers

./manage.py handeling_crawl_uncrawled_behandelde_kamerstukken
