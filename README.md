# parlhist

`parlhist` (working title) is a Python application intended to enable more empirical and statistical
academic studies of Dutch parliamentary minutes and documents. `parlhist` was initially developed at
the [Department of Constitutional and Administrative Law of Leiden Law School (Leiden University, the
Netherlands)](https://www.universiteitleiden.nl/en/law/institute-of-public-law/constitutional-and-administrative-law) in order to investigate in a more empiric manner the role of the Dutch Constitution in
Dutch parliamentary debates. Afterwards, `parlhist` has been expanded for various different types of research.

`parlhist` enables more empirical study of these documents by providing an accessible an local
interface for various types of official governmental publications. Using `parlhist`, one can easily
download the documents of interest without having to deal with the API. `parlhist` enriches some data
also with extra metadata. Once downloaded and enriched, the user can use `parlhist` to develop their
own experiments.

The data used by `parlhist` is retrieved from the official publications by the Dutch Government.
More information can be found on [the page of this dataset on data.overheid.nl](https://data.overheid.nl/dataset/officiele-bekendmakingen#panel-description).
[The API reference of the SRU API by KOOP can be found here](https://data.overheid.nl/dataset/officiele-bekendmakingen#panel-resources).

If you are new to empirical study of governmental documents, [be sure to check out WetSuite!](https://www.wetsuite.nl/)
WetSuite aims to help scholars to leverage more empirical and NLP-based research methods when studying governmental documents, and has a lot of useful resources on their website.

## When can parlhist be useful for my research?
`parlhist` aims to enable you to help you research official Dutch government publications in the _Staatsblad_, _Kamerstukken_ and _Handelingen_ in a more empirical manner. This tool can help you answers questions like: "Have any amendments that are textually similar to this amendment been previously proposed?", "Is it increasingly common that a parliamentary act allows the government to differentiate the date in which individual clauses enter into force?", or "What is the role of the Constitution in parliamentary debates?". 

Using `parlhist`, you can use Python scripts to for example define the initial selection of publications that you want to manually inspect, or to evaluate if there are trends over time. Note however that it is unrealistic to expect to completely automate your research with `parlhist`: you will generally still need to do some manual inspection or manual labelling of data.

## Data accessible via parlhist
As of the latest version of `parlhist`, the following data can be accessed through it:
* Handelingen (Dutch parliamentary minutes) from parliamentary year 1995-1996 through now.
* Kamerstukken (Dutch parliamentary documents) from calendar year 1995 until now.
* Staatsblad (the main Dutch government gazette) from calendar year 1995 until now.

## Data not yet accessible via parlhist
Not all official publications are accessible via parlhist. Some examples are:
* the Staatscourant
* Parliamentary agendas
* Official publications of decentral government bodies such as municipalities, provinces, and water boards (waterschappen).
* Attachments to the Kamerstukken
* Aanhangselen bij de Handelingen (writter parliamentary questions, "Kamervragen")

## Features
* **Extendible**: `parlhist` can be easily extended, as it is based on the [Django web framework](https://www.djangoproject.com/). Data can be easily queried using the Django database-abstraction API, new experiments can be added as new Django commands, or you could even add a complete interactive web-interface to your experiment.
* **Free and open source**: `parlhist` is available under the European Union Public License v1.2 (EUPL-1.2) or any later version. You can use, study, share and change `parlhist` for any goal. If you share your changes to `parlhist`, you must share these under the EUPL-1.2 or any later version of this license. [Please consult the full license for more information](/LICENSE).
* **Automatic memoization** of crawling results: remote data is saved locally in a raw form. When developing `parlhist`, this allows you to quickly rebuild your local database without sending a lot of outbound network requests.
* **Export data to OpenSearch**: you can automatically export data from `parlhist` to an [OpenSearch](https://opensearch.org/) instance, so that you can use [OpenSearch Dashboards](https://docs.opensearch.org/docs/latest/about/) to interact with the data collected via parlhist, or to use the advanced search endpoints provided by OpenSearch to interact with this data.

## Setting up parlhist to develop and run your own experiments

### Requirements

* A database, preferably PostgreSQL. For small datasets and experiments, SQLite may suffice. But be aware that the software is only tested on PostgreSQL.
* A machine to run `parlhist` on, preferably one that runs a modern Linux distribution. `parlhist` has been known to work on recent versions of Fedora, Debian and Ubuntu. The software might work on other operating systems. On Windows, using Windows Subsystem for Linux (WSL) may be a good option.

### Installation
Clone the repository:
```
$ git clone https://github.com/mastaal/parlhist.git
```

Create a Python environment and install all dependencies:
```
$ cd uitspraken
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -U -r requirements.txt
```
If you want to edit the code, you might want to also install all the dependencies in `development_requirements.txt` as well.
If you are just starting out, using the default database (SQLite) is fine. The database will then be stored in the `parlhist.db` file in the same folder as parlhist.
If you are using a different database such as PostgreSQL, you need to make the appropriate changes to the `DATABASES` variable in `parlhist/settings.py`, so that it is configured to use your database.

Note that you can always get help with all the available Django commands:
```
$ ./manage.py help
```
Or with a specific command:
```
$ ./manage.py help migrate
```

### Preparing the database
Then, we can initialize the database:
```
$ ./manage.py migrate
```

#### Parliamentary minutes
Then, we can populate the database as follows. We can crawl one full parliamentary year of parliamentary minutes of both chambers at once:
```
$ ./manage.py handelingen_crawl_vergaderjaar 2021-2022
```

Once you have crawled the minutes of all the parliamentary years you're interested in, you can download the related parliamentary documents using the following commands:
```
$ ./manage.py handeling_crawl_uncrawled_behandelde_kamerstukdossiers
$ ./manage.py handeling_crawl_uncrawled_behandelde_kamerstukken
```
Depending on how many years of data you have crawled, this may take several hours.

Alternatively, you can run the `initialize_database_handelingen.sh` shell script, which initializes
the database with all Handelingen of both the Eerste Kamer and Tweede Kamer of the parliamentary years
1995/96 through 2024/25, and the related Kamerstukken.

#### Staatsblad
You can crawl all publications in the staatsblad between 2024-01-01 and 2024-12-31 (inclusive) using the following command:
```
$ ./manage.py staatsblad_crawl_year 2024
```

More specific crawling is possible. If you want, you kan write your own query that is compatible with the
[KOOP SRU API](https://data.overheid.nl/sites/default/files/dataset/d0cca537-44ea-48cf-9880-fa21e1a7058f/resources/Handleiding%2BSRU%2B2.0.pdf),
and add only the publications that match that query to your parlhist database. See [the `crawl_all_staatsblad_publicaties_within_koop_sru_query` function in parlhistnl/crawler/staatsblad.py](./parlhistnl/crawler/staatsblad.py) for more information.

To crawl the first thirty available years of Staatsblad publications (1995 through 2024), you can run the `initialize_database_staatsblad.sh` script. Be aware however that will take a long time, and be sure that you are not sending to many requests to KOOPs API.

#### Kamerstukken
You can crawl all publications in the Kamerstukken between 2024-01-01 and 2024-12-31 (inclusive) using the following command:
```
$ ./manage.py kamerstukken_crawl_year 2024
```

Just as with the Staatsblad crawling, more specific crawling is possible by specifying a query that is compatible with the KOOP SRU API. See [the `crawl_all_kamerstukken_within_koop_sru_query` function in parlhistnl/crawler/kamerstuk.py](./parlhistnl/crawler/kamerstuk.py) for more information.

### Note on memoization
By default, `parlhist` stores all responses it gets in a raw format. If you want to re-create your database,
you can quickly rebuild everything from these memoized requests. The downside of this, is that the memoized
requests could technically be outdated. But as long as you're only working with fully completed parliamentary
years, this should not pose a problem.

When no memoized request exists, the crawler will wait some time to prevent overloading the API.

### Note on parallelization
You can parallelize crawling tasks by supplying the `--queue-tasks` flag to commands which support this (if in doubt, specify --help to get help with a command). This wil enqueue crawling tasks with celery. For more information on how to use celery with parlhist, see [the development documentation](./docs/development.md).

### Run your experiments

Now that `parlhist` is installed and the database populated with data, you can run your experiments.
Two main approaches exist to do this. First, you can add a new Django command which runs your experiment
(such as `parlhistnl/management/commands/experiment_1_grondwet.py` we've used). Secondly, you can enter a
Django shell using `$ ./manage.py shell` and export the data you are looking for to some other format (pandas,
json, etc.), and do the data analysis in some other tool (a Jupyter Notebook for example).

### Exporting to OpenSearch
Using the `export_to_opensearch` subcommand you can automatically export `parlhist` data to an OpenSearch instance. If you do not know what OpenSearch is or how to set up your own instance, [check out the official OpenSearch documentation](https://docs.opensearch.org/docs/latest/getting-started/).

For example, to export all Staatsblad objects to your OpenSearch instance:
```
$ ./manage.py export_to_opensearch Staatsblad
```

To learn more about the OpenSearch integration, check out [`export_to_opensearch.py`](./parlhistnl/management/commands/export_to_opensearch.py).

## Publications

None yet. Stay tuned!

## Contribute
You can contribute in various ways to `parlhist`:
* By using `parlhist` for your research and sharing your experience and results.
* By citing `parlhist` when you have used it for a publication.
* By sharing your modifications and additions to the `parlhist` code.
* [By checking out the issue tracker for possible useful contributions!](https://github.com/mastaal/parlhist/issues)
* By telling people about how you have used `parlhist` for your reseach.

## Copyright and license

Parlhist was for the most part written for personal study purposes:

Copyright (c) 2023-2025 Martijn Staal <parlhist [at] martijn-staal.nl>

Some parts were written as part of my employment at Universiteit Leiden:

Copyright (c) 2024-2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>

Regardless, the complete source code is available under the same license:

Available under the European Union Public License v1.2 (EUPL-1.2), or, at your option, any later version.

For other language versions of the EUPL - which are all equally valid - [please visit the website of the European Commission on the EUPL](https://interoperable-europe.ec.europa.eu/collection/eupl/eupl-text-eupl-12).
