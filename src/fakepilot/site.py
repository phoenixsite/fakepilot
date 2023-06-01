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
    extract_contact_info,
    extract_location_info_search,
    extract_categories,
    extract_author_name,
    extract_author_id,
    extract_date,
    extract_rating,
    extract_content,
    find_business_urls,
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

    
class Business:

    def __init__(self, url, trustpilot_url):

        self.reviews = None
        self.country = None
        self.city = None
        self.nreviews = None
        self.score = None
        self.categories = None
        self.address = None
        self.email = None
        self.phone = None
        self.address = None
        self.site_url = trustpilot_url

        self.url = url

        tag = get_html_page(url)
        
        self.url_country = self.url.split('.')[-1]
        self.name = extract_name(tag)

        self.nreviews, self.score = extract_rating_stats(tag)

        loc_info = extract_location_info_search(tag)

        if loc_info:
            self.city = loc_info['city']
            self.country = loc_info['country']

        self.categories = extract_categories(tag)
        contact_data = extract_contact_info(tag)

        try:
            self.email = contact_data['email']
        except KeyError:
            pass

        try:
            self.phone = contact_data['phone']
        except KeyError:
            pass

        try:
            self.address = contact_data['address']
        except KeyError:
            pass

    def __str__(self):
        string = f"Name: {self.name}\nURL: {self.url}\n"\
        f"URL country code: {self.url_country}\n"

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

    def extract_reviews(self, nreviews):

        nodes = find_review_nodes(self.url, nreviews)
        self.reviews = [Review(node) for node in nodes]

    def has_attr(self, required):

        has = True
        count = 0
        import pdb; pdb.set_trace()
        while has and count < len(required):

            if required[count] == 'address':
                has = self.address is not None
            elif required[count] == 'phone':
                has = self.phone is not None
            elif required[count] == 'email':
                has = self.email is not None
            count += 1
            
        return has
            

def make_query(trustpilot_url, query, nbusiness, *restricted):
    
    field_query = parse_query(query)
    string_query = prepare_tquery(field_query)
    urls = find_business_urls(trustpilot_url, string_query, field_query, nbusiness)
    businesses = [Business(url, trustpilot_url) for url in urls]

    if restricted:
        businesses = [b for b in businesses if b.has_attr(restricted)]
    return businesses

def search(query, country="united states", nbusiness=None, *restricted):
    """"""
    trustpilot_url = get_url(country)
    print(restricted)
    return make_query(trustpilot_url, query, nbusiness, *restricted)


