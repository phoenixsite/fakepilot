# Fakepilot
[Trustpilot](https://www.trustpilot.com/) scrapping Python package.
Extract online business reviews and integrate it on your code.
It is based on [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).

## Setup

1. Clone the repository or download the zip package

```
git clone https://github.com/phoenixsite/fakepilot.git
```

2. Install the package with `pip`. This will also install its dependencies.

``` sh
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
fp.search("starbucks", 1, "norge")
```

If it is required that all the results include a specific parameter, e.g.
the phone number or the email address of the company, you can specify
in the `search` function:

```python
fp.search("starbucks", 1, "norge",
		       with_reviews=False, nreviews=1, "phone")
```

It is required to specify the rest of the parameters to use this. This issue
will be fixed on following commits (It does not work at this moment).

Also, the reviews of a Trustpilot company page can be directly extracted
using `get_reviews`. The following block extracts ten reviews from the
specified page:

```python
get_reviews("https://www.trustpilot.com/review/www.starbucks.com", 10)
```

## Warning
I strongly recomment using this scrapper with moderation and carefully.
Searching for multiple expressions in a short period of time can generate
a lot of requests and connections to the Trustpilot servers and may affect the
operation of the website. **Be careful, respectful and responsible with
scrappers online**.