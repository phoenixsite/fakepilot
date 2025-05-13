"""
Defines how the data is scrapped from the Trustpilot site.
"""

# SPDX-License-Identifier: MIT

import re
from datetime import datetime

from bs4 import BeautifulSoup

try:
    import lxml  # pylint: disable=unused-import

    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"


def extract_url(tag):
    """
    Return the URL of the company.

    Trustpilot uses the company registered URL to uniquely identify
    a company. However, they aren't normalized. Sometimes they can be
    ``www.company-site.es`` or ``company-site.es``. URL of the company
    as it is stored in Trustpilot.
    """

    business_url = tag.find(class_=re.compile("styles_websiteUrl"))
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
            "The tag where the score and the number of reviews "
            "are hasn't been found."
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

    contact_elements = tag.find_all(
        "li", class_=re.compile("styles_contactInfoElement")
    )

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
    """Return the company's category list."""
    cat_section = tag.find(class_=re.compile("styles_categoriesList"))
    categories = None

    if cat_section:
        cat_refs = cat_section.find_all(href=re.compile("/categories/"))
        categories = [cat_tag.string for cat_tag in cat_refs]

    return categories


def parse_page(page):
    """
    Parse page with BeautifulSoup.

    Set the ``lxml``'s parser if it is installed. If not,
    the ``html.parser`` is used.

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
    }


def extract_author_name(tag):
    """Extract the review's author's name."""
    consumer_node = tag.find(attrs={"data-consumer-name-typography": "true"})

    if not consumer_node:
        raise ValueError(
            """The tag where the author's name should be isn't
            present."""
        )

    return consumer_node.string.title()


def extract_author_id(tag):
    """Extract the review's author id."""
    consumer_node = tag.find(attrs={"data-consumer-profile-link": "true"})

    if not consumer_node:
        raise ValueError(
            """The tag where the author's id should be isn't
            present."""
        )

    return consumer_node.get("href").removeprefix("/users/")


def extract_rating(tag):
    """Extract the rating in the review."""
    star_rating_node = tag.find(class_=re.compile("star-rating"))

    if not star_rating_node:
        raise ValueError(
            """The tag where the review's rating should be isn't
            present."""
        )

    return float(re.search(r"[0-5]", star_rating_node.img["alt"]).group())


def extract_date(tag):
    """Extract the date the review was posted."""
    date_node = tag.find(attrs={"data-service-review-date-time-ago": "true"})

    if not date_node:
        raise ValueError("The tag where the review's date should be isn't present.")

    return datetime.fromisoformat(date_node["datetime"].split(".")[0])


def extract_content(tag):
    """
    Extract the content or body of the review.

    It is returned in Unicode encoding.
    """
    content_node = tag.find(attrs={"data-service-review-text-typography": "true"})

    if not content_node:

        content_node = tag.find(
            "h2", attrs={"data-service-review-title-typography": "true"}
        )

        if not content_node:
            raise ValueError(
                "The tag where the review's content should be isn't present."
            )

    if content_node.string:
        content = str(content_node.string)
    else:
        content = ""
        for string in content_node.strings:
            content += str(string)

    return content


def extract_review_info(tag):
    """Extract the review's data"""
    return {
        "author_name": extract_author_name(tag),
        "author_id": extract_author_id(tag),
        "star_rating": extract_rating(tag),
        "date": extract_date(tag),
        "content": extract_content(tag),
    }
