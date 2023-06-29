"""
site defines the main operations that enable
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
    find_companies,
    find_review_nodes
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
        self.categories = extract_categories(doc)
        self.email = extract_email(doc)
        self.phone = extract_phone(doc)
        self.address = extract_address(doc)

        if self.address:
            address_els = self.address.split(',')

            self.country = address_els[-1]

            if len(address_els) > 1:
                self.city = address_els[-2]

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

    def tp_url(self):
        return f"{self.site_url}/review/{self.url}"

    def extract_reviews(self, nreviews):

        nodes = find_review_nodes(self.tp_url(), nreviews)
        self.reviews = [Review(node) for node in nodes]

def make_query(tp_url, query, ncompanies, *attrs):
    
    field_query = parse_query(query)
    string_query = prepare_tquery(field_query)
    docs = find_companies(tp_url, string_query,
                              field_query, ncompanies, *attrs)
    
    companies = [Company(doc, tp_url) for doc in docs]

    return companies

def search(query, country="united states", ncompanies=None, *attrs):
    """
    Search for companies with a given query.

    Required attributes in every extracted company can be specified, so
    a company that doesn't cotain any of these attributes will be
    discarded.

    It only returns companies with some score.

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
        raise Exception("A query must be provided.")
    if not country:
        raise Exception(f"A valid country should be provided. The available countries are: {get_countries()}")
    
    tp_url = get_url(country)
    return make_query(tp_url, query, ncompanies, *attrs)


