# Fakepilot

[![CI](https://github.com/phoenixsite/fakepilot/actions/workflows/ci.yml/badge.svg)](https://github.com/phoenixsite/fakepilot/actions/workflows/python-app.yml)


[Trustpilot](https://www.trustpilot.com/) scrapping Python package.
Extract online business reviews and integrate it on your code.
It is based on [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).

## Features
* Extract the information of a company from a Trustpilot page.
* Obtain its reviews with a fine-grained detail.
* The output data is structured in a simple dictionary.

IMPORTANT: fakepilot now doesn't fetch the web pages from Trustpilot. This must be done by the user of the package.

## Usage

The main function is ``extract_info``. You can pass a file containing a Trustpilot HTML page of a company and it returns information, like number
of reviews, phone number or address. Also, you can specify if you want
some of the company's reviews to be extracted.

```python
import fakepilot as fp
fp.extract_info("tests/data/burgerking.no.html")
fp.extract_info("tests/data/burgerking.no.html", with_reviews=True, 2)
```

## Installation

fakepilot is available on Pypi. You can install it with

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

## Documentation

For a detail description of all the options you can visit the [fakepilot's
documentation](https://fakepilot.readthedocs.io/)
or you can build yourself
in ``docs`` with [Sphinx](https://www.sphinx-doc.org/en/master/):

```bash
cd docs
make html
```
