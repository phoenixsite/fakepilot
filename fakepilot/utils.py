"""
This module includes constants and functions that support the main
functionality of fakepilot.
"""

from urllib.parse import urlencode

HTTP_PROT = "https"
BASE_URL = "trustpilot.com"
SEARCH_PAGE = "search"
QUERY_PARAM = "query"
PAGE_PARAM = "page"

# Search results and shown reviews vary between countries
COUNTRY_CODE = [
    "us",
    "uk",
    "es",
    "dk",
    "at",
    "ch",
    "de",
    "au",
    "ca",
    "ie",
    "nz",
    "fi",
    "fr-be",
    "nl-be",
    "fr",
    "it",
    "jp",
    "no",
    "nl",
    "pl",
    "br",
    "pt",
    "se",
]
COUNTRY_NAMES = [
    "united states",
    "united kingdom",
    "espana",
    "danmark",
    "osterreich",
    "schweiz",
    "deutschland",
    "australia",
    "canada",
    "ireland",
    "new zealand",
    "suomi",
    "belgique",
    "belgie",
    "france",
    "italia",
    "japan",
    "norge",
    "nederland",
    "polska",
    "brasil",
    "portugal",
    "sverige",
]
COUNTRIES = dict(zip(COUNTRY_NAMES, COUNTRY_CODE))


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

def get_tp_company_url(country, company_url):
    """Return the full Trustpilot company's URL for a specific country."""
    full_address = get_country_address(country)
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
