#!/bin/bash

# SPDX-FileCopyrightText: 2024-2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
#
# SPDX-License-Identifier: EUPL-1.2

source ./venv/bin/activate
./manage.py migrate

./manage.py handelingen_crawl_vergaderjaar 2024-2025
./manage.py handelingen_crawl_vergaderjaar 2023-2024
./manage.py handelingen_crawl_vergaderjaar 2022-2023
./manage.py handelingen_crawl_vergaderjaar 2021-2022
./manage.py handelingen_crawl_vergaderjaar 2020-2021
./manage.py handelingen_crawl_vergaderjaar 2019-2020
./manage.py handelingen_crawl_vergaderjaar 2018-2019
./manage.py handelingen_crawl_vergaderjaar 2017-2018
./manage.py handelingen_crawl_vergaderjaar 2016-2017
./manage.py handelingen_crawl_vergaderjaar 2015-2016
./manage.py handelingen_crawl_vergaderjaar 2014-2015
./manage.py handelingen_crawl_vergaderjaar 2013-2014
./manage.py handelingen_crawl_vergaderjaar 2012-2013
./manage.py handelingen_crawl_vergaderjaar 2011-2012
./manage.py handelingen_crawl_vergaderjaar 2010-2011
./manage.py handelingen_crawl_vergaderjaar 2009-2010
./manage.py handelingen_crawl_vergaderjaar 2008-2009
./manage.py handelingen_crawl_vergaderjaar 2007-2008
./manage.py handelingen_crawl_vergaderjaar 2006-2007
./manage.py handelingen_crawl_vergaderjaar 2005-2006
./manage.py handelingen_crawl_vergaderjaar 2004-2005
./manage.py handelingen_crawl_vergaderjaar 2003-2004
./manage.py handelingen_crawl_vergaderjaar 2002-2003
./manage.py handelingen_crawl_vergaderjaar 2001-2002
./manage.py handelingen_crawl_vergaderjaar 2000-2001
./manage.py handelingen_crawl_vergaderjaar 1999-2000
./manage.py handelingen_crawl_vergaderjaar 1998-1999
./manage.py handelingen_crawl_vergaderjaar 1997-1998
./manage.py handelingen_crawl_vergaderjaar 1996-1997
./manage.py handelingen_crawl_vergaderjaar 1995-1996

./manage.py handeling_crawl_uncrawled_behandelde_kamerstukdossiers

./manage.py handeling_crawl_uncrawled_behandelde_kamerstukken
