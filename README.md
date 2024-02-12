# parlhist

`parlhist` (working title) is a Python application intended to enable more empirical and statistical
academic studies of parliamentary documents. It is developed at the Institute of Public Law of the
Leiden Law School (Leiden University, the Netherlands), in order to investigate in a more empiric manner
the role of the Dutch Constitution in Dutch parliamentary debates.

The data used by this program is retrieved from the official publications by the Dutch Government.
More information can be found on [the page of this dataset on data.overheid.nl](https://data.overheid.nl/dataset/officiele-bekendmakingen#panel-description). [The API reference of the SRU API by KOOP can be found here](https://data.overheid.nl/sites/default/files/dataset/d0cca537-44ea-48cf-9880-fa21e1a7058f/resources/Handleiding%2BSRU%2B2.0.pdf).

## Current features

Currently, `parlhist` can be used to easily crawl all the Dutch parliamentary minutes (Handelingen) and
related documents (Kamerstukken). These documents are stored in a database and can be easily queried
using the Django database-abstraction API (or by querying the database directly).

## Planned ideas

* More advanced natural language processing to get more insight than just counting matches.
* Support for decentralized democratic bodies in the Netherlands (Provinciale Staten, Gemeenteraden, Algemeen besturen van Waterschappen).


## Publications

None yet. Stay tuned!

## License

Copyright (c) 2023, 2024 Martijn Staal/Universiteit Leiden <m.a.staal [at] law.leidenuniv.nl> / <parlhist [at] martijn-staal.nl>

Available under the European Union Public License v1.2 (EUPL-1.2), or, at your option, any later version.
