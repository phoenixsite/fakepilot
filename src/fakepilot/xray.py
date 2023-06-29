"""
xray defines how the data is scrapped from the Trustpilot
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


def find_companies_urls(tp_url, string_query, field_query, nbusiness):
    """
    Get the Trustpilot urls of the companies that match the requested
    query.

    :param tp_url: Trustpilot url
    :type url: str
    :param string_query: Prepared query string
    :type string_query: str
    :param field_query: Required values for each clause included in the
    query.
    :type field_query: dict of str, str
    :rparam: Trustpilot companies urls that match the query.
    :rtype: list of str
    """

    r = request.urlopen(f"{tp_url}{SEARCH_EXT}{string_query}")
    parsed_page = BeautifulSoup(r, PARSER)

    max_npages = get_npages(parsed_page)
    current_page, urls = 1, []
    
    while current_page <= max_npages and len(urls) < nbusiness:

        page_param = "" if current_page == 1 else f"&page={current_page}"
        
        r = request.urlopen(
            f"{tp_url}{SEARCH_EXT}{string_query}{page_param}")
        search_page = BeautifulSoup(r, PARSER)

        current_nodes = search_page.find_all(
            href=re.compile("/review/"), limit=(nbusiness - len(urls)))

        if 'city' in field_query:

            current_nodes = [node for node in current_nodes
                     if extract_location_info_search(node)
                     and re.search(
                         field_query['city'],
                         extract_location_info_search(node)['city'],
                         re.IGNORECASE)
                     and re.search(
                         field_query['country'],
                         extract_location_info_search(node)['country'],
                         re.IGNORECASE)]

        if 'name' in field_query:
            current_nodes = [node for node in current_nodes
                     if re.search(
                             field_query['name'],
                             extract_name_search(node),
                             re.IGNORECASE)]

        urls.extend([f"{tp_url}{node.get('href')}" for node in current_nodes])
        current_page += 1
        
    return urls

def extract_name_search(doc):
    """
    Extract the company name from a search page.

    Used to discard companies that doesn't match the name query clause.
    """
    
    name_tag = doc.find('p', class_=re.compile('styles_displayName'))
    return name_tag.string

def extract_location_info_search(tag):
    """
    Extract the city and country location from the search page.

    Used to discard companies that doesn't match the city query clause.
    """

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


class CompanyDoc(BeautifulSoup):
    """
    Represents the HTML page of a company as a BeautifulSoup data
    structure.

    Used to avoid double checkings when restrictions over the
    attributes of a company are imposed. When an attribute is
    extracted from the HTML page for the first time, then it is
    saved in the object next extractions doesn't need to analyze
    again the page.
    """

    def __init__(self, markup, parser):
        BeautifulSoup.__init__(self, markup, parser)
        self.attrs = {}

    def __contains__(self, item):

        if item == 'phone':
            self.extract_phone()
        elif item == 'email':
            self.extract_email()
        elif item == 'address':
            self.extract_address()
        elif item == 'categories':
            self.extract_categories()
        elif item == 'score':
            self.extract_score()
        elif item == 'nreviews':
            self.extract_nreviews()
        elif item == 'name':
            self.extract_name()
        
        return item in self.attrs and self.attrs[item]

    def extract_url(self):

        if 'url' not in self.attrs:
            business_url = self.find(class_=re.compile('styles_websiteUrl'))
            url = ""

            for string in business_url.strings:
                url += string

            self.attrs['url'] = url
        return self.attrs['url']
    
    def extract_name(self):

        if 'name' not in self.attrs:
            name_tag = self.find('h1', class_=re.compile('title_title'))
            self.attrs['name'] = next(name_tag.find(
                class_=re.compile('title_displayName')).strings)

        return self.attrs['name']
    
    def __extract_rating_stats(self):

        if 'score' not in self.attrs or 'nreviews' not in self.attrs:
            nreviews_tag = self.find(
                attrs={'data-reviews-count-typography': 'true'})
    
            if nreviews_tag.string:
                nreviews = nreviews_tag.string.split()[0]
            else:
                nreviews = next(nreviews_tag.strings)

            nreviews = nreviews.replace(',', "")
            nreviews = int(nreviews)
    
            score_tag = self.find(attrs={'data-rating-typography': 'true'})
            score = float(score_tag.string.replace(",", "."))
            self.attrs['nreviews'] = nreviews
            self.attrs['score'] = score

    def extract_nreviews(self):

        self.__extract_rating_stats()
        return self.attrs['nreviews']

    def extract_score(self):

        self.__extract_rating_stats()
        return self.attrs['score']

    def __extract_contact_info(self):
        """
        Extract the contact information (address, phone number,
        city, country, ...) of a company.
        """
        
        if 'email' not in self.attrs or 'phone' not in self.attrs or 'address' not in self.attrs:       
            def is_sideColumn(css_class):
                return css_class is not None and 'styles_sideColumnCard' in css_class and 'paper_paper' in css_class
        
            info_tag = self.find(class_=is_sideColumn)
            address_tag = info_tag.find('address')
        
            parsed_data = {'phone': None, 'email': None, 'address': None}

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

            for contact_key in parsed_data:
                self.attrs[contact_key] = parsed_data[contact_key]

    def extract_email(self):

        self.__extract_contact_info()
        return self.attrs['email']

    def extract_phone(self):

        self.__extract_contact_info()
        return self.attrs['phone']

    def extract_address(self):

        self.__extract_contact_info()
        return self.attrs['address']

    def extract_categories(self):

        if 'categories' not in self.attrs:

            cat_section = self.find(class_=re.compile('styles_categoriesList'))
            categories = None
    
            if cat_section:
                cat_refs = cat_section.findAll(href=re.compile('/categories/'))
                categories = [cat_tag.string for cat_tag in cat_refs]

            self.attrs['categories'] = categories
        
        return self.attrs['categories']


def extract_url(doc):
    """
    Extract the business URL

    It never returns None, as a Trustpilot business always has a URL.
    """
    
    return doc.extract_url()

def extract_name(doc):
    """
    Extract the name from the business page.

    It never return None, as a Trustpilot business always has a name.
    """
    
    return doc.extract_name()

def extract_nreviews(doc):
    """
    Extract the number of reviews about the company.
    """
    
    return doc.extract_nreviews()

def extract_score(doc):
    """
    Extract the score of the company.
    """

    return doc.extract_score()

def extract_email(doc):
    """
    Extract the email. None is returned if it isn't published.
    """
    
    return doc.extract_email()

def extract_phone(doc):
    """
    Extract the phone number. None is returned if it isn't published.
    """
    
    return doc.extract_email()

def extract_address(doc):
    """
    Extract the address as a string. The found address fields are joined
    with a comma.

    The address may be partially completed, depending on the fields displyed
    on the page. The city and country where the company is located are the
    most common address fields, but neither they always appear.
    """
    
    return doc.extract_address()

def extract_categories(doc):
    """
    Extract the categories of a business. Info extracted from the
    business page.
    """

    return doc.extract_categories()    

def get_html_page(url):
    """
    Fetch the page of the given url, which stands for a company page.
    """
    
    return CompanyDoc(request.urlopen(url), PARSER)

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

    content_node = tag.find(
        attrs={"data-service-review-text-typography": "true"})

    if not content_node:

        content_node = tag.find(
            "h2",
            attrs={"data-service-review-title-typography": "true"})

    if content_node.string:
        content = content_node.string.encode()
    else:
        content = bytes()
        for string in content_node.strings:
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

def find_review_nodes(company_url, nreviews):
    """Get the HTML nodes that cotains the reviews of a business"""

    r = request.urlopen(company_url)
    parsed_page = BeautifulSoup(r, PARSER)

    max_npages = get_npages(parsed_page)
    current_page, nodes = 1, []

    while current_page <= max_npages and len(nodes) < nreviews:

        page_param = "" if current_page == 1 else f"&page={current_page}"

        r = request.urlopen(f"{company_url}{page_param}")
        parsed_page = BeautifulSoup(r, PARSER)

        nodes.extend(parsed_page.find_all(
            class_=re.compile("styles_reviewCardInner"),
            limit=(nreviews - len(nodes))))

        current_page += 1

    return nodes
