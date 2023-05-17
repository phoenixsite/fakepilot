import urllib.request as request
from bs4 import BeautifulSoup
import re

PARSER = 'lxml'

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
COUNTRY_NAMES = ["united states", "united kingdom", "españa",
                      "danmark", "österreich", "schweiz",
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

def prepare_query(base_query):
    """Transform the query so it is compatible with the search pattern
    used in a Trustpilot URL"""
    base_query = base_query.replace(" ", "+")
    return base_query

def find_business_node(parsed_page):
    """Get the HTML business card list"""
    return parsed_page.find_all(href=re.compile("/review/"))

class Business:

    def __init__(self, tag):

        self.country = None
        self.city = None
        self.nreviews = None
        self.score = None

        self.url = tag.get('href').removeprefix('/review/')
        self.url_country = self.url.split('.')[-1]

        name_tag = tag.find_all('p',
                                class_=re.compile('typography_heading'))[0]
        self.name = name_tag.string

        rating_section = tag.find_all(class_=re.compile('styles_rating'))

        # Check if rating business info is shown
        if rating_section:

            rating_section = rating_section[0]
            score_string = rating_section.find_all(
                class_=re.compile('styles_trustScore'))[0].strings

            # Attribute strings is a generator and it is needed only the
            # last element: the score number
            score_string = [string for string in score_string][-1]
            self.score = float(score_string)
        
            nreviews_string = rating_section.find_all(
                string=re.compile(r'[\d,]'))[-1]

            # When there is just one review, there is no HTML comment,
            # so the previuos regex result in '1 review'. This situation
            # is checked manually
            if len(nreviews_string.split()) > 1:
                nreviews_string = nreviews_string.split()[0]
                
            nreviews_string = nreviews_string.replace(",", "")
            self.nreviews = int(nreviews_string)

        location_section = tag.find_all(class_=re.compile('styles_location'))

        # Check if location business info is shown
        if location_section:
            location_section = location_section[0]

            # Contain HTML comments in the middle of the string
            # so this must be deleted
            location = [string for string in location_section.strings]
            self.city, self.country = location[0], location[-1]

    def __str__(self):
        string = f"Name: {self.name}\nURL: {self.url}\n"\
        f"URL country code: {self.url_country}\n"

        if self.score:
            string += f"Score: {self.score}\n"
        if self.city:
            string += f"City: {self.city}\n"
        if self.country:
            string += f"Country: {self.country}\n"
        return string

    
def make_query(url, query):

    r = request.urlopen(f"{url}{SEARCH_EXT}{query}")
    parsed_page = BeautifulSoup(r, PARSER)
    nodes = find_business_node(parsed_page)
    return [Business(node) for node in nodes]
    
def search_sites(country, query):
    """"""
    url = get_url(country)
    query = prepare_query(query)
    return make_query(url, query)
    
if __name__ == '__main__':

    country = "united kingdom"
    query = "burger y ahora"
    businesses = search_sites(country, query)
    for business in businesses:
        print(business)
