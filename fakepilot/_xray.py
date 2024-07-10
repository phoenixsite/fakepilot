"""
This module defines how the data is scrapped from the Trustpilot site.
"""

import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

PARSER = "lxml"
REVIEW_CLASS = re.compile("styles_reviewCardInner")
BUSINESS_CLASS = re.compile("businessUnitResult")

# Used to speed up the BeautifulSoup detection of the markup encoding
TPENCODING = "utf-8"


def has_attrs(tag, attrs):
    """
    Check that a company has registered on Trustpilot some attributes`.

    :param tag: HTML tag that should contain SVG icons.
    :type tag: :class:`bs4.Tag`
    :param attrs: Required attributes that the company must include.
    :type attrs: list[str] or str
    :return: ``True`` if all `attrs` are contained in `tag`, ``False`` otherwise.
    """

    # The existence of an attribute is done checking if the icon of that attribute
    # appears on the node. The 'd' attribute of the tag 'path' is used.
    d_attrs = {
        "email": """M0 2.5h16v11H0v-11Zm1.789 1L8 9.173 14.211 3.5H1.79ZM15
        4.134l-7 6.393-7-6.393V12.5h14V4.134Z""",
        "phone": """m4.622.933.04.057.003.006L6.37 3.604l.002.003a1.7 1.7 0 0
        1-.442 2.29l-.036.029c-.392.325-.627.519-.652.85-.026.364.206 1.09
        1.562 2.445 1.356 1.357 2.073 1.58 2.426
        1.55.318-.027.503-.252.816-.632l.057-.069a1.7 1.7 0 0 1
        2.29-.442l.003.002 2.608
        1.705.006.004c.204.141.454.37.649.645.188.267.376.655.31
        1.09-.031.213-.147.495-.305.774a4.534 4.534 0 0 1-.715.941C14.323
        15.422 13.377 16 12.1
        16c-1.236 0-2.569-.483-3.877-1.246-1.315-.768-2.642-1.84-3.877-3.075C3.112
        10.444 2.033 9.118 1.26 7.8.49 6.49 0 5.15 0 3.9c0-1.274.52-2.215
        1.144-2.845C1.751.442 2.478.098 2.954.03c.507-.072.896.088
        1.182.327.224.187.387.43.486.576Zm-1.127.191a.46.46 0 0
        0-.4-.104c-.223.032-.758.25-1.24.738C1.393 2.227 1 2.924 1 3.9c0
        1.001.398 2.161 1.122 3.394.72 1.226 1.74 2.486 2.932 3.678 1.19
        1.19 2.45 2.204 3.673 2.918 1.23.718 2.384 1.11 3.373 1.11.949 0
        1.652-.422 2.138-.914.245-.247.43-.508.556-.73.134-.237.181-.393.186-.43.01-.065-.014-.19-.139-.366a1.737 1.737
        0 0 0-.396-.396l-2.59-1.693a.7.7 0 0
        0-.946.19l-.011.017-.013.016-.08.098c-.261.33-.723.91-1.491.975-.841.07-1.85-.47-3.218-1.838-1.369-1.37-1.912-2.381-1.85-3.225.056-.783.638-1.25.97-1.517l.09-.072.016-.013.016-.011a.7.7
        0 0 0 .191-.946l-1.694-2.59-.051-.076c-.104-.152-.182-.265-.29-.355Z""",
        "address": """M8 4a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5ZM4.5 6.5a3.5 3.5
        0 1 1 7 0 3.5 3.5 0 0 1-7 0Z""",
    }

    include_all = True

    if isinstance(attrs, str):
        attrs = [attrs]

    for attr in attrs:
        icon = tag.find("path", d=d_attrs[attr])

        if not icon:
            include_all = False

    return include_all


def extract_nreviews_score_search(tag):
    """
    Extract the number of reviews and score of a business from
    the search page.

    :param tag: HTML tag analyzed.
    :type tag: :class:`bs4.Tag`
    :return: Number of reviews and Trustscore of a company.
    :rtype: tuple(float, int)
    """

    rating_tag = tag.find(class_=re.compile("ratingText"))
    mini_box = list(rating_tag.stripped_strings)
    return (mini_box[1], mini_box[3])


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

    contact_elements = tag.findAll("li", class_=re.compile("styles_contactInfoElement"))

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
        cat_refs = cat_section.findAll(href=re.compile("/categories/"))
        categories = [cat_tag.string for cat_tag in cat_refs]

    return categories


def get_npages(tag):
    """
    Get the number of pages from the search's result page.

    :param tag: HTML tag of a result-like page.
    :type tag: :class:`bs4.Tag`
    :return: the number of pages.
    :rtype: int
    """

    npage_button_section = tag.find("nav", class_=re.compile("pagination_pagination"))

    if not npage_button_section:
        raise ValueError(
            """The HTML section where the number of pages is not
                         present."""
        )

    # The last page button has a specific name if there are more than three
    # pages.
    last_page_button = npage_button_section.find(
        attrs={"name": "pagination-button-last"}
    )

    # If there are less than three pages, then the last page button
    # doesn't have any specific attribute, so the last button is chosen.
    if not last_page_button:
        last_page_button = npage_button_section.contents[-2]

    # If the last button attribute href does
    # not have a query parameter named 'page', it means there is only
    # one page
    try:
        npages = int(parse_qs(urlparse(last_page_button["href"]).query)["page"][0])
    except KeyError:
        npages = 1

    return npages


def parse_page(page, only_class):
    """
    Parse page with BeautifulSoup.

    Set the lxml's parser and the parse_only parameter of
    the BeautifulSoup constructor, if passed.

    :param page: HTML document to be parsed.
    :type page: str
    :param only_class: Type of tags to be analysed.
    :type only_class: :class:`bs4.SoupStrainer`
    :return: Parsed page with BeautifulSoup class.
    :rtype: :class:`bs4.BeautifulSoup`
    """

    return BeautifulSoup(
        page,
        PARSER,
        from_encoding=TPENCODING,
        parse_only=only_class,
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
        content = content_node.string.encode()
    else:
        content = bytes()
        for string in content_node.strings:
            content += string.encode()

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
