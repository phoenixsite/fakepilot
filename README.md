[![CI](https://github.com/phoenixsite/fakepilot/actions/workflows/ci.yml/badge.svg)](https://github.com/phoenixsite/fakepilot/actions?query=workflow%3ACI)


[Trustpilot](https://www.trustpilot.com/) scraping Python package.
Extract online business reviews and integrate it on your code.
It is based on [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).

## Features
* Extract the information of a company from a Trustpilot page.
* Obtain its reviews with a fine-grained detail.
* The output data is structured in a simple dictionary.
* Support for Trustpilot pages with different HTML structure.

IMPORTANT: fakepilot now doesn't fetch the web pages from Trustpilot. This must be done by the user of the package.

## Usage

The main function is ``extract_info``. You can pass a file containing a Trustpilot HTML page of a company and it returns information, like number
of reviews, phone number or address. Also, you can specify if you want
some of the company's reviews to be extracted.

```python
import fakepilot as fp

# Company information only
with open("company_page.html", encoding="utf-8") as page:
    company = fp.extract_info(page)

# Company information plus its first 2 reviews
with open("company_page.html", encoding="utf-8") as page:
    company = fp.extract_info(page, with_reviews=True, nreviews=2)

print(company["name"], company["score"], company["nreviews"])
print(company["reviews"][0]["title"])
```

``extract_info`` expects an open file (or a string with the HTML content),
not a path. ``company_page.html`` is a company's Trustpilot page that you
have saved yourself, e.g. ``https://www.trustpilot.com/review/<company-domain>``
saved from your browser.

## Installation

fakepilot is available on [PyPI](https://pypi.org/project/fakepilot/). You can install it with

```bash
python -m pip install fakepilot
```

To install fakepilot from the GitHub source, clone the repository with `git`:

```bash
git clone https://github.com/phoenixsite/fakepilot.git
```

Then, change your current directory to the one you cloned and install it with `pip`:

```bash
cd fakepilot
python -m pip install .
```

## Documentation

For a detail description of all the options you can visit the [fakepilot's
documentation](https://fakepilot.readthedocs.io/)
or you can build yourself
in ``docs`` with [Sphinx](https://www.sphinx-doc.org/en/master/):

```bash
cd docs
python -m pip install -r requirements.txt
make html
```
