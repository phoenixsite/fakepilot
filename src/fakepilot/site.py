"""
site.py defines the main operations that enable
the access to the scrapped data.
"""

from .utils import get_url
from .query import (
    prepare_tquery,
    parse_query)

from .xray import (
    extract_name,
    extract_rating_stats,
    extract_url,
    extract_location_info,
    extract_author_name,
    extract_author_id,
    extract_date,
    extract_rating,
    extract_content,
    find_business_nodes,
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

    
class Business:

    def __init__(self, tag, site_url):

        self.reviews = None
        self.country = None
        self.city = None
        self.nreviews = None
        self.score = None
        self.site_url = site_url

        self.url = extract_url(tag)
        self.url_country = self.url.split('.')[-1]
        self.name = extract_name(tag)

        stats = extract_rating_stats(tag)

        if stats:
            self.score = stats['score']
            self.nreviews = stats['nreviews']

        loc_info = extract_location_info(tag)

        if loc_info:
            self.city = loc_info['city']
            self.country = loc_info['country']

    def __str__(self):
        string = f"Name: {self.name}\nURL: {self.url}\n"\
        f"URL country code: {self.url_country}\n"

        if self.score:
            string += f"Score: {self.score}\n"
        if self.city:
            string += f"City: {self.city}\n"
        if self.country:
            string += f"Country: {self.country}\n"

        if self.reviews:
            string += "Reviews:\n"

            for count, review in enumerate(self.reviews):
                string += f"Review {count}:\n{review}\n"
                
        return string

    def get_review_url(self):
        return f"{self.site_url}/review/{self.url}?languages=all"

    def extract_reviews(self, nreviews):
        
        nodes = find_review_nodes(self.get_review_url(), nreviews)
        self.reviews = [Review(node) for node in nodes]

def make_query(url, query, nbusiness):

    field_query = parse_query(query)
    string_query = prepare_tquery(field_query)
    nodes = find_business_nodes(url, string_query, field_query, nbusiness)
    return [Business(node, url) for node in nodes]

def search_sites(country, query, nbusiness=None):
    """"""
    url = get_url(country)
    return make_query(url, query, nbusiness)
