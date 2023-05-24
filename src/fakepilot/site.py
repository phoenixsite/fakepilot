import urllib.request as request
from bs4 import BeautifulSoup
import re
from datetime import datetime

from .utils import (get_url, SEARCH_EXT)
from .query import (
    prepare_tquery,
    parse_query)

from .xray import (
    extract_name,
    extract_rating_stats,
    extract_url,
    extract_location_info,
    extract_author,
    extract_date,
    extract_rating,
    extract_content)

PARSER = 'lxml'

def find_business_node(parsed_page, field_query):
    """Get the HTML nodes that contains the business information"""

    nodes =  parsed_page.find_all(href=re.compile("/review/"))

    if 'city' in field_query:

        nodes = [node for node in nodes
                           if extract_location_info(node)
                 and re.search(
                     field_query['city'],
                     extract_location_info(node)['city'],
                     re.IGNORECASE)
                 and re.search(
                     field_query['country'],
                     extract_location_info(node)['country'],
                     re.IGNORECASE)]

    if 'name' in field_query:
        nodes = [node for node in nodes
                 if re.search(field_query['name'], extract_name(node), re.IGNORECASE)]
    return nodes

def find_review_nodes(parsed_page):
    """Get the HTML nodes that cotains the reviews of a business"""
    return parsed_page.find_all(class_=re.compile("styles_reviewCardInner"))


class Review:

    def __init__(self, tag):

        self.author = extract_author(tag)
        self.star_rating = extract_rating(tag)
        self.date = extract_date(tag)
        self.content = extract_content(tag)

    def __str__(self):
        
        string = f"Author: {self.author}\nRating: {self.star_rating}\n"\
            f"Date: {self.date}\nContent: {self.content}"
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
        return f"{self.site_url}/review/{self.url}"

    def extract_reviews(self):
        r = request.urlopen(self.get_review_url())
        parsed_page = BeautifulSoup(r, PARSER)
        nodes = find_review_nodes(parsed_page)
        self.reviews = [Review(node) for node in nodes]

def make_query(url, query):

    field_query = parse_query(query)
    string_query = prepare_tquery(field_query)
    r = request.urlopen(f"{url}{SEARCH_EXT}{string_query}")
    parsed_page = BeautifulSoup(r, PARSER)
    nodes = find_business_node(parsed_page, field_query)
    return [Business(node, url) for node in nodes]

def search_sites(country, query):
    """"""
    url = get_url(country)
    return make_query(url, query)
