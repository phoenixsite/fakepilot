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
    """Extract the business URL. Info extracted from the
    search page."""
    return tag.get('href').removeprefix('/review/')

def extract_name(tag):
    """Extract the business name. Info extracted from
    the business page."""
    
    name_tag = tag.find('h1', class_=re.compile('title_title'))
    return next(name_tag.find(class_=re.compile('title_displayName')).strings)

def extract_rating_stats(tag):
    """Extract the TrustScore and the number of reviews. Info extracted
    from the business page."""

    nreviews_tag = tag.find(attrs={'data-reviews-count-typography': 'true'})
    
    if nreviews_tag.string:
        nreviews = nreviews_tag.string.split()[0]
    else:
        nreviews = next(nreviews_tag.strings)

    nreviews = nreviews.replace(',', "")
    nreviews = int(nreviews)
    
    score_tag = tag.find(attrs={'data-rating-typography': 'true'})
    score = float(score_tag.string)
    return nreviews, score

def extract_location_info_search(tag):
    """Extract the business city and country location. Info extracted
    from the search page."""

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

def extract_contact_info(tag):
    """Extract the contact information (address, phone number,
    city, country, ...) of a busisness. Info extracted from the
    business page."""

    def is_sideColumn(css_class):
        return css_class is not None and 'styles_sideColumnCard' in css_class and 'paper_paper' in css_class
    
    info_tag = tag.find(class_=is_sideColumn)
    address_tag = info_tag.find('address')
    
    parsed_data = {}

    if address_tag:

        contact_elements = address_tag.findAll(
            'li',
            class_=re.compile('styles_contactInfoElement'))

        reg_fields = [('phone', re.compile(r'^\+?\d[\d-]+')),
                      ('email', re.compile(
                          r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')),
                      ]
        
        for contact_info in contact_elements:

            line = ",".join([s for s in contact_info.strings])
            field = None
            count = 0
        
            while not field and count < len(reg_fields):

                if reg_fields[count][1].search(line):
                    field = reg_fields[count][0]
                
                count += 1
            
            if not field:
                field = 'address'
            
            parsed_data[field] = line

    return parsed_data

def extract_categories(tag):
    """Extract the categories of a business. Info extracted from the
    business page."""
    pass

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
        search_page = BeautifulSoup(r, PARSER)

        current_nodes = search_page.find_all(
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
