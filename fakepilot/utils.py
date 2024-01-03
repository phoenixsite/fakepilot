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
COUNTRY_CODE = ["us", "uk", "es", "dk",
                   "at", "ch", "de", "au",
                   "ca", "ie", "nz", "fi",
                   "fr-be", "nl-be", "fr", "it",
                   "jp", "no", "nl", "pl", "br",
                   "pt", "se"]
COUNTRY_NAMES = ["united states", "united kingdom", "espana",
                      "danmark", "osterreich", "schweiz",
                      "deutschland", "australia", "canada",
                      "ireland", "new zealand", "suomi",
                      "belgique", "belgie", "france", "italia",
                      "japan", "norge", "nederland", "polska",
                      "brasil", "portugal", "sverige"]
COUNTRIES = dict(zip(COUNTRY_NAMES, COUNTRY_CODE))

def check_country(country_code):
    """Check if a country code is between those available is Trustpilot."""
    if not country_code:
        raise ValueError("""The selected country is not available in
        Trustpilot""")

def get_tp_search_url(country, string_query, npage=None):
    """Return the URL of the Trustpilot's search page."""
    country_code = COUNTRIES[country.casefold()]
    check_country(country_code)

    query_values = {QUERY_PARAM: string_query}

    if npage and npage != 1:
        query_values["page"] = npage

    url = f"{HTTP_PROT}://{country_code}.{BASE_URL}/{SEARCH_PAGE}"
    data = urlencode(query_values)
    return f"{url}?{data}"

def get_tp_company_url(country, company_url):
    """Return the full Trustpilot company's URL for a specific country."""
    country_code = COUNTRIES[country.casefold()]
    check_country(country_code)
    return f"{HTTP_PROT}://{country_code}.{BASE_URL}/{company_url}?languages=all"
