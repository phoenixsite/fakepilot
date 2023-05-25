"""
xray.py defines how the data is scrapped from the Trustpilot
site. It checks different HTML and CSS elements to find where
the data is displayed.
"""

from bs4 import BeautifulSoup
import re
from datetime import datetime

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
