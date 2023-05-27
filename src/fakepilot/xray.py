"""
xray.py defines how the data is scrapped from the Trustpilot
site. It checks different HTML and CSS elements to find where
the data is displayed.
"""

import urllib.request as request
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import re
from datetime import datetime

from .utils import SEARCH_EXT

PARSER = 'html.parser'


def extract_url(tag):
    """Extract the business URL"""
    return tag.get('href').removeprefix('/review/')

def extract_name(tag):
    """Extract the business name"""
    return tag.find('p', class_=re.compile('typography_heading')).string

def extract_rating_stats(tag):
    """Extract the TrustScore and the number of reviews"""

    rating_section = tag.find_all(class_=re.compile('styles_rating'))
    stats = {}
    # Check if rating business info is shown
    if rating_section:

        rating_section = rating_section[0]
        score_string = rating_section.find_all(
            class_=re.compile('styles_trustScore'))[0].strings

        # Attribute strings is a generator and it is needed only the
        # last element: the score number
        score_string = [string for string in score_string][-1]
        stats['score'] = float(score_string.replace(',', '.'))

        nreviews_string = rating_section.find_all(
            string=re.compile(r'[\d,]'))[-1]

        # When there is just one review, there is no HTML comment,
        # so the previuos regex result in '1 review'. This situation
        # is checked manually
        if len(nreviews_string.split()) > 1:
            nreviews_string = nreviews_string.split()[0]
            
        nreviews_string = nreviews_string.replace(",", "").replace(".", "")
        stats['nreviews'] = int(nreviews_string)

    return stats

def extract_location_info(tag):
    """Extract the business city and country location."""

    location_section = tag.find_all(class_=re.compile('styles_location'))
    loc_info = None
    
    # Check if location business info is shown
    if location_section:
        loc_info = {}
        location_section = location_section[0]

        # Contain HTML comments in the middle of the string
        # so this must be deleted
        location = [string for string in location_section.strings]
        loc_info['city'] = location[0].capitalize()
        loc_info['country'] = location[-1].capitalize()

    return loc_info

def extract_author_name(tag):
    """Extract the review author name"""
    consumer_node = tag.find(
        attrs={"data-consumer-name-typography": "true"})
    return consumer_node.string.title()

def extract_author_id(tag):
    """Extract the review author id"""
    consumer_node = tag.find(
        attrs={"data-consumer-profile-link": "true"})
    return consumer_node.get('href').removeprefix('/users/')

def extract_rating(tag):
    """Extract the rating given in the review"""
    star_rating_node = tag.find(class_=re.compile('star-rating'))
    return float(re.search(r'[0-5]', star_rating_node.img['alt']).group())

def extract_date(tag):
    """Extract the date the review was written"""
    date_node = tag.find(
        attrs={"data-service-review-date-time-ago": "true"})
    return datetime.fromisoformat(date_node['datetime'].split('.')[0])

def extract_content(tag):
    """Extract the content or body of the review"""

    review_content_node = tag.find(
        attrs={"data-service-review-text-typography": "true"})

    if review_content_node.string:
        content = review_content_node.string.encode()
    else:
        content = bytes()
        for string in review_content_node.strings:
            content += string.encode()

    return content

def get_npages(tag):
    """
    Get the number of pages of results.

    If there are more than five result pages,
    then a three-dot button is displayed and the last
    button will have a 'pagination-button-last' name attribute.
    If not, then the button name attribute will be numbered
    """

    npage_button_section = tag.find(
        'nav', class_=re.compile('pagination_pagination'))

    last_page_button = npage_button_section.find(
        attrs={'name':'pagination-button-last'})

    if not last_page_button:
        last_page_button = npage_button_section.contents[-2]

    # If a KeyError is raised, then the last button attribute href does
    # not have a query parameter named 'page', which means there is only
    # one page
    try:
        npages = int(parse_qs(urlparse(
            last_page_button['href']).query)['page'][0])
    except KeyError:
        npages = 1
    
    return npages
    
def find_business_nodes(url, string_query, field_query, nbusiness):
    """Get the HTML nodes that contains the business information"""

    r = request.urlopen(f"{url}{SEARCH_EXT}{string_query}")
    parsed_page = BeautifulSoup(r, PARSER)

    max_npages = get_npages(parsed_page)
    current_page, nodes = 1, []
    
    while current_page <= max_npages and len(nodes) < nbusiness:

        page_param = "" if current_page == 1 else f"&page={current_page}"
        
        r = request.urlopen(
            f"{url}{SEARCH_EXT}{string_query}{page_param}")
        parsed_page = BeautifulSoup(r, PARSER)

        current_nodes = parsed_page.find_all(
            href=re.compile("/review/"), limit=(nbusiness - len(nodes)))

        if 'city' in field_query:

            current_nodes = [node for node in current_nodes
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
            current_nodes = [node for node in current_nodes
                     if re.search(
                             field_query['name'],
                             extract_name(node),
                             re.IGNORECASE)]

        nodes.extend(current_nodes)
        current_page += 1
        
    return nodes

def find_review_nodes(url, nreviews):
    """Get the HTML nodes that cotains the reviews of a business"""

    r = request.urlopen(url)
    parsed_page = BeautifulSoup(r, PARSER)

    max_npages = get_npages(parsed_page)
    current_page, nodes = 1, []

    while current_page <= max_npages and len(nodes) < nreviews:

        page_param = "" if current_page == 1 else f"&page={current_page}"

        r = request.urlopen(f"{url}{page_param}")
        parsed_page = BeautifulSoup(r, PARSER)

        nodes.extend(parsed_page.find_all(
            class_=re.compile("styles_reviewCardInner"),
            limit=(nreviews - len(nodes))))

        current_page += 1

    return nodes
