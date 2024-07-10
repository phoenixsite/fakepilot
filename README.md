# Fakepilot

[![Build Status](https://github.com/phoenixsite/fakepilot/actions/workflows/python-app.yml/badge.svg)](https://github.com/phoenixsite/fakepilot/actions/workflows/python-app.yml)
[![Supported Python
versions](https://img.shields.io/pypi/pyversions/fakepilot.svg)](https://pypi.org/project/fakepilot/)

[Trustpilot](https://www.trustpilot.com/) scrapping Python package.
Extract online business reviews and integrate it on your code.
It is based on [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).

## Features
* Simple searching functionalitites.
* Support the selection of any country available in Trustpilot.
* Extraction of fine-grained data from business reviews.
* Use Trustpilot URLs or local file from where extract the information.

## Installation
[![PyPI version](https://badge.fury.io/py/fakepilot.svg)](https://pypi.org/project/fakepilot/)

fakepilot is available on `pip`. You can install fakepilot from it with

```bash
pip install fakepilot
```

To install fakepilot from the GitHub source, clone the repository with `git`:

```bash
git clone https://github.com/phoenixsite/fakepilot.git
```

Then, change your current directory to the one you cloned and install it with `pip`:

```bash
cd fakepilot
pip install .
```

## Usage
The function `search` can be used to mimic the search bar functionality
of Trustpilot. It limits the number of results and you can
indicate whether some reviews should be extracted for each company result.
For example, the following code search for two companies that match
the expression 'starbucks' and two of its reviews.

``` python
import fakepilot as fp
fp.search("starbucks", 2, with_reviews=True, nreviews=2)
```

All the Trustpilot country-specific sites can be used to make the queries.
For instance, the Norwegian Trustpilot site can be used:

``` python
fp.search("starbucks", 1, country="norge")
```

If it is required that all the results include a specific parameter, e.g.
the phone number of the company, you can specify it
in the `search` function:

```python
fp.search("starbucks", 1, False, 1, "phone", "norge")
```

Also, the information of a Trustpilot company page can be directly extracted
using ``get_company`` with a given URL or a local file.
The following block extracts ten reviews from the
specified URL:

```python
get_company("https://www.trustpilot.com/review/www.starbucks.com", 10)
```

The following block extract the information and ten reviews from a local file:

```python
get_company("my_file.html", True, 10)
```

## Documentation
For a detail description of all the options you can visit the [fakepilot's
official documentation site](https://fakepilot.readthedocs.io/)
or you can build yourself
in ``docs`` with [Sphinx](https://www.sphinx-doc.org/en/master/):

```bash
cd docs
make html
```

## Warning
I strongly recommend using this scrapper with moderation and carefully.
Searching for multiple expressions in a short period of time can generate
a lot of requests and connections to the Trustpilot servers and may affect the
operation of the website. **Be careful, respectful and responsible with
scrappers online**.
