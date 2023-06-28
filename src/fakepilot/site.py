"""
site.py defines the main operations that enable
the access to the scrapped data.
"""

__docformat__ = 'restructuredtext'

from functools import reduce
from .utils import get_url, get_countries
from .query import (
    prepare_tquery,
    parse_query)

from .xray import (
    extract_url,
    extract_name,
    extract_nreviews,
    extract_score,
    extract_email,
    extract_phone,
    extract_address,
    extract_location_info_search,
    extract_categories,
    extract_author_name,
    extract_author_id,
    extract_date,
    extract_rating,
    extract_content,
    find_companies_urls,
    find_review_nodes,
    get_html_page
)


class Review:

    def __init__(self, tag):
        
        self.author_name = extract_author_name(tag)
        self.author_id = extract_author_id(tag)
        self.star_rating = extract_rating(tag)
        self.date = extract_date(tag)
        self.content = extract_content(tag)

    def __str__(self):
        
        string = f"Author name: {self.author_name}\nAuthor id: {self.author_id}\n"
        string += f"Rating: {self.star_rating}\n"
        string += f"Date: {self.date}\nContent: {self.content}"
        return string

class Company:

    def __init__(self, doc, trustpilot_url):

        self.reviews = None
        self.country = None
        self.city = None
        self.site_url = trustpilot_url

        self.url = extract_url(doc)
        self.name = extract_name(doc)
        self.nreviews, self.score = extract_nreviews(doc), extract_score(doc)

        #loc_info = extract_location_info_search(tag)

        #if loc_info:
        #    self.city = loc_info['city']
        #    self.country = loc_info['country']

        self.categories = extract_categories(doc)
        self.email = extract_email(doc)
        self.phone = extract_phone(doc)
        self.address = extract_address(doc)

    def __str__(self):
        string = f"Name: {self.name}\nURL: {self.url}\n"

        if self.score:
            string += f"Score: {self.score}\n"
        if self.city:
            string += f"City: {self.city}\n"
        if self.country:
            string += f"Country: {self.country}\n"

        if self.categories:
            string += "Categories:\n"

            for cat in self.categories:
                string += f"\t{cat}\n"
            string += "\n"

        if self.email:
            string += f"Email: {self.email}\n"

        if self.phone:
            string += f"Phone number: {self.phone}\n"
            
        if self.address:
            string += f"Address: {self.address}\n"
        
        if self.reviews:
            string += "Reviews:\n"

            for count, review in enumerate(self.reviews):
                string += f"Review {count}:\n{review}\n"
                
        return string

    def get_company_url(self):
        return f"{self.site_url}/review/{self.url}"

    def extract_reviews(self, nreviews):

        nodes = find_review_nodes(self.get_company_url(), nreviews)
        self.reviews = [Review(node) for node in nodes]
                

def has_attrs(doc, *attrs):
    """
    Check if all the attributes attrs are in the company page doc.

    :param doc: Extracted company page
    :type doc: xray.CompanyDoc
    :param attrs: Required attributes
    :type attrs: list of str
    :rparam True if all attrs is contained in doc, False otherwise.
    """
    attrs = list(attrs)
    return reduce(lambda x, y: x and y, [attr in doc for attr in attrs], True)
    

def make_query(tp_url, query, ncompanies, *attrs):
    
    field_query = parse_query(query)
    string_query = prepare_tquery(field_query)
    urls = find_companies_urls(tp_url, string_query,
                              field_query, ncompanies)
    
    docs = [get_html_page(url) for url in urls]
    docs = [doc for doc in docs if has_attrs(doc, *attrs)]
    companies = [Company(doc, tp_url) for doc in docs]

    return companies

def search(query, country="united states", ncompanies=None, *attrs):
    """
    Search for companies with a given query.

    Required attributes in every extracted company can be specified, so
    a company that doesn't cotain any of these attributes will be
    discarded.

    :param query: Query string. It should contain at least one word and
    query clauses can be specified (E.g. 'city: Los Angeles,
    name: Burger').
    :type query: str
    :param country: Country name whose Trustpilot webite is used to
    apply the query.
    :type country: str
    :param ncompanies: Maximum number of companies extracted.
    :type ncompanies: int
    :param attrs: Required attributes for every company.
    :type attrs: list of str 
    :rparam: List of extracted companies.
    :rtype: list of Companies
    """

    if not query:
        raise Exception("A query must be provided")
    if not country:
        raise Exception(f"A valid country should be provided. The available countries are: {get_countries()}")
    
    tp_url = get_url(country)
    return make_query(tp_url, query, ncompanies, *attrs)


