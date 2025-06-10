#!/bin/bash

# SPDX-FileCopyrightText: 2025 Martijn Staal <parlhist [at] martijn-staal.nl>
# SPDX-FileCopyrightText: 2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>
#
# SPDX-License-Identifier: EUPL-1.2

if [ "$1" = '--queue-tasks' ]; then
    ARGS='--update --queue-tasks'
else
    ARGS='--update'
fi

./manage.py staatsblad_crawl_year 2024 $ARGS
./manage.py staatsblad_crawl_year 2023 $ARGS
./manage.py staatsblad_crawl_year 2022 $ARGS
./manage.py staatsblad_crawl_year 2021 $ARGS
./manage.py staatsblad_crawl_year 2020 $ARGS
./manage.py staatsblad_crawl_year 2019 $ARGS
./manage.py staatsblad_crawl_year 2018 $ARGS
./manage.py staatsblad_crawl_year 2017 $ARGS
./manage.py staatsblad_crawl_year 2016 $ARGS
./manage.py staatsblad_crawl_year 2015 $ARGS
./manage.py staatsblad_crawl_year 2014 $ARGS
./manage.py staatsblad_crawl_year 2013 $ARGS
./manage.py staatsblad_crawl_year 2012 $ARGS
./manage.py staatsblad_crawl_year 2011 $ARGS
./manage.py staatsblad_crawl_year 2010 $ARGS
./manage.py staatsblad_crawl_year 2009 $ARGS
./manage.py staatsblad_crawl_year 2008 $ARGS
./manage.py staatsblad_crawl_year 2007 $ARGS
./manage.py staatsblad_crawl_year 2006 $ARGS
./manage.py staatsblad_crawl_year 2005 $ARGS
./manage.py staatsblad_crawl_year 2004 $ARGS
./manage.py staatsblad_crawl_year 2003 $ARGS
./manage.py staatsblad_crawl_year 2002 $ARGS
./manage.py staatsblad_crawl_year 2001 $ARGS
./manage.py staatsblad_crawl_year 2000 $ARGS
./manage.py staatsblad_crawl_year 1999 $ARGS
./manage.py staatsblad_crawl_year 1998 $ARGS
./manage.py staatsblad_crawl_year 1997 $ARGS
./manage.py staatsblad_crawl_year 1996 $ARGS
./manage.py staatsblad_crawl_year 1995 $ARGS
