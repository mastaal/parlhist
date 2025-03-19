# parlhist

`parlhist` (working title) is a Python application intended to enable more empirical and statistical
academic studies of parliamentary minutes and documents. It is developed at the Institute of Public Law of the
Leiden Law School (Leiden University, the Netherlands), in order to investigate in a more empiric manner
the role of the Dutch Constitution in Dutch parliamentary debates.

The data used by this program is retrieved from the official publications by the Dutch Government.
More information can be found on [the page of this dataset on data.overheid.nl](https://data.overheid.nl/dataset/officiele-bekendmakingen#panel-description). [The API reference of the SRU API by KOOP can be found here](https://data.overheid.nl/sites/default/files/dataset/d0cca537-44ea-48cf-9880-fa21e1a7058f/resources/Handleiding%2BSRU%2B2.0.pdf).

## Current features

Currently, `parlhist` can be used to easily crawl all the Dutch parliamentary minutes (Handelingen) and
related documents (Kamerstukken). These documents are stored in a database and can be easily queried
using the Django database-abstraction API (or by querying the database directly). Additionally, new
Django commands can be written to write automated experiments.

## Planned ideas

* More advanced natural language processing to get more insight than just counting matches.
* Support for decentralized democratic bodies in the Netherlands (Provinciale Staten, Gemeenteraden, Algemeen besturen van Waterschappen).
* Web interface to make queries
* Store experiment results in database
* Support for parliamentary history from before parliamentary year 2011-2012

## Requirements

* A database, preferably PostgreSQL. For small datasets and experiments, SQLite may suffice. But be aware that the software is only tested on PostgreSQL.
* A machine to run `parlhist` on, preferably a (recent) Linux machine. The software might work on other operating systems.

## Usage

### Installation
Clone the repository:
```
$ git clone https://github.com/mastaal/uitspraken.git
```

Create a Python environment and install all dependencies:
```
$ cd uitspraken
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -U -r requirements.txt
```
If you want to edit the code, you might want to also install all the dependencies in `development_requirements.txt` as well.
Then, make the appropriate changes to the `DATABASES` variable in `parlhist/settings.py`, so that it is configured to use your database.

### Preparing the database
Then, we can initialize the database:
```
$ ./manage migrate
```

Then, we can populate the database as follows. Currently it is only possible to crawl one full year of parliamentary history at once:
```
$ ./manage vergaderdag_crawl_full_vergaderjaar --kamer tk 20212022
```

Once you have crawled all the parliamentary years you're interested in, you can download the related parliamentary documents using the following commands:
```
$ ./manage handeling_crawl_uncrawled_behandelde_kamerstukdossiers
$ ./manage handeling_crawl_uncrawled_behandelde_kamerstukken
```
Depending on how many years of data you have crawled, this may take several hours.

Alternatively, you can run the `initialize_database.sh` shell script, which initializes the database with
all Handelingen of both the Eerste Kamer and Tweede Kamer of the parliamentary years 2011/2012 through 2022/2023, and the related Kamerstukken.

### Note on memoization
By default, `parlhist` stores all responses it gets in a raw format. If you want to re-create your database,
you can quickly rebuild everything from these memoized requests. The downside of this, is that the memoized
requests could technically be outdated. But as long as you're only working with fully completed parliamentary
years, this should not pose a problem.

When no memoized request exists, the crawler will wait some time to prevent overloading the API.

### Run your experiments

Now that `parlhist` is installed and the database populated with data, you can run your experiments.
Two main approaches exist to do this. First, you can add a new Django command which runs your experiment
(such as `parlhistnl/management/commands/experiment_1_grondwet.py` we've used). Secondly, you can enter a
Django shell using `$ ./manage shell` and export the data you are looking for to some other format (pandas,
json, etc.), and do the data analysis in some other tool (a Jupyter Notebook for example).

## Publications

None yet. Stay tuned!

## Copyright and license

Parlhist was for the most part written for personal study purposes:
Copyright (c) 2023-2025 Martijn Staal <parlhist [at] martijn-staal.nl>

Some parts were written as part of my employment at Universiteit Leiden:
Copyright (c) 2024-2025 Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl>

Regardless, the complete source code is available under the same license:
Available under the European Union Public License v1.2 (EUPL-1.2), or, at your option, any later version.
