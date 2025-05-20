"""
Defines how the data is scrapped from the Trustpilot site.
"""

# SPDX-License-Identifier: MIT

import re
import datetime
from functools import reduce
import operator

from bs4 import BeautifulSoup

try:
    import lxml  # pylint: disable=unused-import

    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"


def has_attr(attr_name):
    """Return a function that checks if a tag has an attribute."""
    return lambda tag: tag.has_attr(attr_name)


def extract_url(tag):
    """
    Return the URL of the company.

    Trustpilot uses the company registered URL to uniquely identify
    a company. However, they aren't normalized. Sometimes they can be
    ``www.company-site.es`` or ``company-site.es``. URL of the company
    as it is stored in Trustpilot.
    """

    # For May 2025 pages
    business_url = tag.find(class_=re.compile("link_internal"))

    return "".join(business_url.strings)


def extract_company_name(tag):
    """Return the name of the company."""
    return next(tag.find(class_=re.compile("title_displayName")).strings)


def extract_rating_stats(tag):
    """
    Extract the number of reviews and the TrustScore.

    Both attributes are extracted simultaneously because they
    are in the same tag.
    """

    nreviews_tag = tag.find(attrs={"data-reviews-count-typography": "true"})

    if not nreviews_tag:
        raise RuntimeError(
            "The tag where the score and the number of reviews are hasn't been found."
        )

    nreviews = (
        nreviews_tag.string.split()[0]
        if nreviews_tag.string
        else next(nreviews_tag.strings)
    )

    # The thousand separator is different for some countries
    nreviews = re.sub(r"[.,\xa0]", "", nreviews)
    score_tag = tag.find(attrs={"data-rating-typography": "true"})
    score = score_tag.string.replace(",", ".")
    return (int(nreviews), float(score))


def extract_contact_info(tag):
    """
    Extract the phone, address and email fields.

    :return: A pair whose first element is the phone number, then
             the email and finally the address.
    """

    phone = email = address = None

    # As the address field does not have a specific structure,
    # the other two are searched and the last one would the
    # address field
    phone_re = re.compile(r"^\+?\d[\d-]+")
    email_re = re.compile(
        r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
    )

    # For May 2025 pages
    contact_elements = tag.find_all("li", class_=re.compile("styles_itemRow"))

    # For December 2023 pages
    if not contact_elements:
        contact_elements = tag.find_all(
            "li", class_=re.compile("styles_contactInfoElement")
        )
    else:
        # On modern pages the last element is the company's URL,
        # so we ned to remove it from the contact element list.
        contact_elements = contact_elements[:-1]

    for contact_info in contact_elements:
        line = ",".join(contact_info.strings)

        if phone_re.search(line):
            phone = line
        elif email_re.search(line):
            email = line
        else:
            address = line

    return (phone, email, address)


def extract_categories(tag):
    """
    Return the company's category list.
    """

    cat_refs = tag.find_all(has_attr("data-business-unit-info-category-typography"))
    categories = [cat_tag.string for cat_tag in cat_refs]

    return categories


def extract_is_claimed(tag):
    """
    Indicate if the Trustpilot company's page is claimed by the company.
    """

    claimed_tag = tag.find(string=re.compile("Claimed profile"))
    return True if claimed_tag else False


def parse_page(page):
    """
    Parse page with BeautifulSoup.

    Set the ``lxml``'s parser if it is installed. If not, the ``html.parser``
    is used.

    :param page: HTML document to be parsed.
    :type page: str
    :return: Parsed page with BeautifulSoup class.
    :rtype: :class:`bs4.BeautifulSoup`
    """

    return BeautifulSoup(
        page,
        PARSER,
        from_encoding="utf-8",
    )


def extract_company_info(tag):
    """Extract the data of a company."""
    try:
        nreviews, score = extract_rating_stats(tag)
    except RuntimeError:
        score = nreviews = None

    phone, email, address = extract_contact_info(tag)

    return {
        "name": extract_company_name(tag),
        "url": extract_url(tag),
        "nreviews": nreviews,
        "score": score,
        "categories": extract_categories(tag),
        "email": email,
        "phone": phone,
        "address": address,
        "is_claimed": extract_is_claimed(tag),
    }


def extract_review_author_name(tag):
    """Extract the review's author's name."""
    consumer_node = tag.find(attrs={"data-consumer-name-typography": "true"})
    return consumer_node.string


def extract_review_author_id(tag):
    """Extract the review's author id."""
    consumer_node = tag.find(attrs={"data-consumer-profile-link": "true"})

    # The author link is https://www.trustpilot.com/users/66642b4....954121bbb4cc643
    return consumer_node.get("href").rsplit("/", 1)[-1]


def extract_review_rating(tag):
    """Extract the rating in the review."""
    attr_name = "data-service-review-rating"
    star_rating_node = tag.find(has_attr(attr_name))
    return float(star_rating_node.attrs[attr_name])


def extract_review_date(tag):
    """Extract the date the review was posted."""
    date_node = tag.find(attrs={"data-service-review-date-time-ago": "true"})
    return datetime.datetime.strptime(date_node["datetime"], "%Y-%m-%dT%H:%M:%S.%fZ")


def extract_review_title(tag):
    """Extract the title of the review."""
    title_node = tag.find(has_attr("data-service-review-title-typography"))
    return title_node.string.strip()


def concat_strings(node):
    """
    Concat the strings contained in ``node`` as a unique and complete string.

    We need to check if there is just one or more strings. In case of the
    latter, then we need to concate them.
    See https://www.crummy.com/software/BeautifulSoup/bs4/doc/#string
    """

    if node.string:
        concat_string = str(node.string)
    else:
        concat_string = reduce(operator.add, node.strings)
    return concat_string


def extract_review_content(tag):
    """
    Extract the content or body of the review.

    It is returned in Unicode encoding.
    """

    content_node = tag.find(attrs={"data-service-review-text-typography": "true"})

    if not content_node:
        content = ""
    else:
        content = concat_strings(content_node)
        content = content.replace("\n", "").strip()

    return content


def extract_number_reviews_author(tag):
    """
    Extract the number of reviews made by the author of the current review.
    """

    attr = "data-consumer-reviews-count"
    nreviews_node = tag.find(has_attr(attr))
    return int(nreviews_node.attrs[attr])


def extract_authors_country(tag):
    """
    Extract the country where the author is from.
    """

    country_node = tag.find(attrs={"data-consumer-country-typography": "true"})
    country = concat_strings(country_node)
    return country


def extract_date_experience(tag):
    """
    Extract the date of experience of the review.
    """

    exp_node = tag.find(
        attrs={"data-service-review-date-of-experience-typography": "true"}
    )
    exp_date_str = concat_strings(exp_node)
    exp_date_str = exp_date_str.split(":")[-1].strip()
    return datetime.datetime.strptime(exp_date_str, "%B %d, %Y")


def extract_is_verified(tag):
    """
    Extract if the review is verified.
    """

    ver_node = tag.find(attrs={"data-review-label-tooltip-trigger-typography": "true"})
    return True if ver_node else False


def extract_review_info(tag):
    """Extract the review's data"""
    return {
        "author_name": extract_review_author_name(tag),
        "author_id": extract_review_author_id(tag),
        "is_verified": extract_is_verified(tag),
        "star_rating": extract_review_rating(tag),
        "date": extract_review_date(tag),
        "title": extract_review_title(tag),
        "content": extract_review_content(tag),
        "nreviews": extract_number_reviews_author(tag),
        "country": extract_authors_country(tag),
        "date_experience": extract_date_experience(tag),
    }
