"""
This module includes constants and functions that support the main
functionality of fakepilot.
"""

from urllib.parse import urlencode
from urllib import request


HTTP_PROT = "https"
BASE_URL = "trustpilot.com"
SEARCH_PAGE = "search"
QUERY_PARAM = "query"
PAGE_PARAM = "page"

COUNTRIES = {
    "united states": "us",
    "united kingdom": "uk",
    "espana": "es",
    "danmark": "dk",
    "osterreich": "at",
    "schweiz": "ch",
    "deutschland": "de",
    "australia": "au",
    "canada": "ca",
    "ireland": "ie",
    "new zealand": "nz",
    "suomi": "fi",
    "belgique": "fr-be",
    "belgie": "nl-be",
    "france": "fr",
    "italia": "it",
    "japan": "jp",
    "norge": "no",
    "nederland": "nl",
    "polska": "pl",
    "brasil": "br",
    "portugal": "pt",
    "sverige": "se",
}


def pretty_countries():
    """Return a human-readable listing of the available countries."""
    all_countries = [country.title() for country in COUNTRIES.keys()]
    s = ", ".join(all_countries[: len(all_countries) - 1])
    s = f"{s} and {all_countries[-1]}"
    return s


def normalize(country):
    """Normalize the input country."""
    return country.casefold()


def check_country(country):
    """Check if a country code is between those available in Trustpilot."""
    country_code = COUNTRIES[normalize(country)]

    if not country_code:
        raise ValueError("The selected country is not available in Trustpilot")


def get_country_address(country):
    """
    Get the Trustpilot address of the selected country.

    The Trustpilot address of each country is prefixed by the country code
    followed by the Trustpilot main address, except for the US, which is
    only the main address.
    """
    check_country(country)
    country_code = COUNTRIES[normalize(country)]
    return f"www.{BASE_URL}" if country_code == "us" else f"{country_code}.{BASE_URL}"


def get_search_url(country, string_query, npage=1):
    """Return the URL of the Trustpilot's search page."""
    full_address = get_country_address(country)

    query_values = {PAGE_PARAM: npage} if npage != 1 else {}
    query_values[QUERY_PARAM] = string_query

    url = f"{HTTP_PROT}://{full_address}/{SEARCH_PAGE}"
    data = urlencode(query_values)
    return f"{url}?{data}"


def get_tp_company_url(company_url, country="us"):
    """
    Return the full Trustpilot company's URL for a specific country.

    :param company_url: Trustpilot company's subpage (review/my-site.com) or
           id of the company (my-site.com).
    :type company_url: str
    """
    full_address = get_country_address(country)

    if len(company_url.split("/")) == 1:
        company_url = f"/review/{company_url}"

    return f"{HTTP_PROT}://{full_address}{company_url}?languages=all"


def get_company_url_paged(tp_company_url, npage=1):
    """
    Return the full company's Trustpilot URL at some of its pages.

    :param tp_company_url:
    :type tp_company_url: str
    :param npage: Pgae number of the company's reviews.
    :type npage: int
    :return: Company's Trustpilot URL paged.
    :rtype: str
    """
    return f"{tp_company_url}&page={npage}" if npage != 1 else tp_company_url


def construct_request(url):
    """Construct a request for the given url."""
    # Artificial header. TODO: Random generation of headers and
    # inter-request time.
    hdr = {
        "User-Agent": """Mozilla/5.0 (Windows NT 10.0; Win64; x64;
            rv:102.0) Gecko/20100101 Firefox/102.0"""
    }
    return request.Request(url, headers=hdr)
