HTTP_PROT = "https"
BASE_URL = "trustpilot.com"
SEARCH_EXT = "/search?query="

# Search results vary between countries
COUNTRY_CODE = ["us", "uk", "es", "dk",
                   "at", "ch", "de", "au",
                   "ca", "ie", "nz", "fi",
                   "fr-be", "fr", "it",
                   "jp", "no", "nl", "pl", "br",
                   "pt", "se"]
COUNTRY_NAMES = ["united states", "united kingdom", "espana",
                      "danmark", "osterreich", "schweiz",
                      "deutschland", "australia", "canada",
                      "ireland", "new zealand", "suomi",
                      "belgique", "france", "italia",
                      "japan", "norge", "nederland", "polska",
                      "brasil", "portugal", "sverige"]
COUNTRIES = dict(zip(COUNTRY_NAMES, COUNTRY_CODE))

def get_url(country):
    """Get the URL of Trustpilot site given the country"""

    country = country.casefold()
    country_code = COUNTRIES[country]
    if not country_code:
        raise Exception("""The selected country is not available in
        Trustpilot""")

    return f"{HTTP_PROT}://{country_code}.{BASE_URL}"

def get_countries():
    """Get the human-readable list of countries available in Trustpilot"""

    all_countries = [country.title() for country in COUNTRY_NAMES]
    s = ", ".join(all_countries[:len(all_countries) - 1])
    s = f"{s} and {all_countries[-1]}"
    return s
    
    
