"""
xray defines how the data is scrapped from the Trustpilot
site. It checks different HTML and CSS elements to find where
the data is displayed.
"""

from functools import reduce
import urllib.request as request
from urllib.parse import urlencode, parse_qs, urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime
from fakepilot.utils import get_tp_company_url, get_tp_search_url

PARSER = 'html.parser'


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

def extract_name_search(doc):
    """
    Extract the company name from a search page.

    It is used to discard companies that doesn't match the name query clause.
    """
    
    name_tag = doc.find('p', class_=re.compile('styles_displayName'))
    return name_tag.string

def extract_location_info_search(tag):
    """
    Extract the city and country location from the search page.

    It is used to discard companies that doesn't match the city query clause.
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

            # The thousand separator is different for some countries
            nreviews = int(re.sub(r'[.,\xa0]', '', nreviews))
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


def get_html_page(url):
    """
    Fetch the page of the given url, which stands for a company page.
    """
    
    return CompanyDoc(request.urlopen(url), PARSER)

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
    
def get_companies_info(country, string_query, field_query, nbusiness, *attrs):
    """
    Get the Trustpilot data of the companies that match the requested
    query.

    :param country: Country whose Trustpilot page is used to scrape. 
    :type country: str
    :param string_query: Prepared query string.
    :type string_query: str
    :param field_query: Required values for each clause included in the
    query.
    :type field_query: dict of str, str
    :param attrs: Required attributes in a company. If a company does not
    include some of the ones in attr, it is discarded. 
    :type attrs: list of str
    :rparam: Trustpilot companies that match the query. The commpany url is used
    as the key of the dictionary.
    :rtype: dict of (str, dict(str,))
    """
    
    # Change to request binding method
    url = get_tp_search_url(country, string_query)
    r = request.urlopen(url)
    parsed_page = BeautifulSoup(r, PARSER)

    max_npages = get_npages(parsed_page)
    current_page, companies = 1, {}
    
    while current_page <= max_npages and len(companies) < nbusiness:

        # Artificial header. TODO: Random generation of headers and inter-request time. 
        hdr = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0' }
        url = get_tp_search_url(country, string_query, current_page)
        req = request.Request(url, headers=hdr)
        search_page = BeautifulSoup(request.urlopen(req), PARSER)

        current_nodes = search_page.find_all(
            href=re.compile("/review/"), limit=(nbusiness - len(companies)))

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

        for node in current_nodes:
            
            # Added ?languages=all to make sure all the ratings are shown
            tp_comp_url = get_tp_company_url(country, node.get('href'))
            comp_page = get_html_page(tp_comp_url)

            if not attrs or (attrs and has_attrs(comp_page, *attrs)):

                company = {
                    "name": comp_page.extract_name(),
                    "url": comp_page.extract_url(),
                    "nreviews": comp_page.extract_nreviews(),
                    "score": comp_page.extract_score(),
                    "categories": comp_page.extract_categories(),
                    "email": comp_page.extract_email(),
                    "phone": comp_page.extract_phone(),
                    "address": comp_page.extract_address()
                }
                company["tp_url"] = tp_comp_url
                companies[company["url"]] = company

        current_page += 1
        
    return companies

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

def get_reviews(company_url, nreviews):

    r = request.urlopen(company_url)
    parsed_page = BeautifulSoup(r, PARSER)

    max_npages = get_npages(parsed_page)
    current_page, reviews = 1, []

    while current_page <= max_npages and len(reviews) < nreviews:

        page_param = "" if current_page == 1 else f"&page={current_page}"

        r = request.urlopen(f"{company_url}{page_param}")
        parsed_page = BeautifulSoup(r, PARSER)

        nodes = parsed_page.find_all(
            class_=re.compile("styles_reviewCardInner"),
            limit=(nreviews - len(reviews)))

        for node in nodes:
            reviews.append({
                "author_name": extract_author_name(node),
                "author_id": extract_author_id(node),
                "star_rating": extract_rating(node),
                "date": extract_date(node),
                "content": extract_content(node),
            })
        
        current_page += 1

    return reviews
