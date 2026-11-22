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
    import lxml  # noqa: F401  # pylint: disable=unused-import

    PARSER = "lxml"  # pragma: no cover (depends on the optional lxml)
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


def extract_rating_stats_v1(tag):
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
    # Phone numbers can be written like +34 600-000-000 or (855) 470-1527
    phone_re = re.compile(r"^\s*\+?\(?\d[\d\s().-]{4,}\d\s*$")
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
    categories = []

    for cat_tag in cat_refs:
        # On 2026 pages, if the company is ranked in a category, the tag
        # contains a text like "#4 of 7 best companies in <a>Category</a>",
        # so the category's name is the text of the link
        name_tag = cat_tag.find("a") or cat_tag
        categories.append(name_tag.get_text().strip())

    return categories


def extract_is_claimed(tag):
    """
    Indicate if the Trustpilot company's page is claimed by the company.
    """

    claimed_tag = tag.find(string=re.compile("Claimed profile"))
    return bool(claimed_tag)


def extract_percentage_stars(tag):
    """
    Extract the percentage of reviews that the company has received for each
    rating (1 star, 2 stars, etc.).
    """

    rating_dist_str = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    rating_dist = dict(
        zip(range(1, len(rating_dist_str.keys()) + 1), [None] * len(rating_dist_str))
    )

    # The rating distribution information is in a side panel. Also,
    # there are other tags in the page with the attributes data-star-rating,
    # so that's why we need to get first the side panel
    side_info_tag = tag.find(class_=re.compile("styles_businessInfoSideBar"))

    if side_info_tag:
        for number_stars_str, nstars in rating_dist_str.items():
            rating_tag = side_info_tag.find(
                attrs={"data-star-rating": number_stars_str}
            )

            if rating_tag:
                bar_tag = rating_tag.find(
                    class_=re.compile("rating-distribution-row_barValue")
                )
                percentage = bar_tag.attrs["style"].split(":")[-1].rstrip("%")
                rating_dist[nstars] = float(percentage)

    if any(percentage is not None for percentage in rating_dist.values()):
        return rating_dist
    return None


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

    return BeautifulSoup(page, PARSER)


def parse_company_v1(tag):
    """Extract the data of a company."""
    try:
        nreviews, score = extract_rating_stats_v1(tag)
    # On old Trsutpilot pages, if the company closed
    # then the company's page does not show the score or
    # number of reviews
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
        "rating_distribution": extract_percentage_stars(tag),
    }


def extract_review_author_name_v1(tag):
    """Extract the review's author's name."""
    consumer_node = tag.find(attrs={"data-consumer-name-typography": "true"})
    return consumer_node.string


def extract_review_author_id_v1(tag):
    """Extract the review's author id."""
    consumer_node = tag.find(attrs={"data-consumer-profile-link": "true"})

    # The author link is https://www.trustpilot.com/users/66642b4....954121bbb4cc643
    return consumer_node.get("href").rsplit("/", 1)[-1]


def extract_review_rating_v1(tag):
    """Extract the rating in the review."""
    attr_name = "data-service-review-rating"
    star_rating_node = tag.find(has_attr(attr_name))
    return float(star_rating_node.attrs[attr_name])


def extract_review_date_v1(tag):
    """Extract the date the review was posted."""
    date_node = tag.find(attrs={"data-service-review-date-time-ago": "true"})
    return datetime.datetime.strptime(date_node["datetime"], "%Y-%m-%dT%H:%M:%S.%fZ")


def extract_review_title_v1(tag):
    """Extract the title of the review."""
    title_node = tag.find(has_attr("data-service-review-title-typography"))
    return title_node.string.strip()


def concat_strings(node):
    """
    Concatenate the strings contained in ``node`` as a unique and complete
    string.

    We need to check if there is just one or more strings. In case of the
    latter, then we need to concatenate them.
    See https://www.crummy.com/software/BeautifulSoup/bs4/doc/#string
    """

    if node.string:
        concat_string = str(node.string)
    else:
        concat_string = reduce(operator.add, node.strings)
    return concat_string


def extract_review_content_v1(tag):
    """
    Extract the content or body of the review.

    It is returned in Unicode encoding.
    """

    content_node = tag.find(attrs={"data-service-review-text-typography": "true"})

    if not content_node:
        content = ""
    else:
        # content = concat_strings(content_node)
        # content = content.replace("\n", "").strip()
        content = content_node.get_text()

    return content


def extract_number_reviews_author_v1(tag):
    """
    Extract the number of reviews made by the author of the current review.
    """

    attr = "data-consumer-reviews-count"
    nreviews_node = tag.find(has_attr(attr))
    return int(nreviews_node.attrs[attr])


def extract_authors_country_v1(tag):
    """
    Extract the country where the author is from.
    """

    country_node = tag.find(attrs={"data-consumer-country-typography": "true"})

    if not country_node:
        raise RuntimeError("The tag containing the review's country hasn't been found.")

    country = concat_strings(country_node)
    return country


def extract_date_experience_v1(tag):
    """
    Extract the date of experience of the review.
    """

    exp_node = tag.find(
        attrs={"data-service-review-date-of-experience-typography": "true"}
    )

    if not exp_node:
        raise RuntimeError(
            "The tag containing the review's experience date was not found."
        )

    exp_date_str = concat_strings(exp_node)
    exp_date_str = exp_date_str.split(":")[-1].strip()
    return datetime.datetime.strptime(exp_date_str, "%B %d, %Y")


def extract_is_verified_v1(tag):
    """
    Extract if the review is verified.
    """

    ver_node = tag.find(attrs={"data-review-label-tooltip-trigger-typography": "true"})
    return bool(ver_node)


def extract_review_info_v1(tag):
    """Extract the review's data"""
    return {
        "author_name": extract_review_author_name_v1(tag),
        "author_id": extract_review_author_id_v1(tag),
        "is_verified": extract_is_verified_v1(tag),
        "star_rating": extract_review_rating_v1(tag),
        "date": extract_review_date_v1(tag),
        "title": extract_review_title_v1(tag),
        "content": extract_review_content_v1(tag),
        "nreviews": extract_number_reviews_author_v1(tag),
        "country": extract_authors_country_v1(tag),
        "date_experience": extract_date_experience_v1(tag),
    }


def extract_rating_stats_v2(tag):
    """
    Extract the number of reviews and the TrustScore.

    Both attributes are extracted simultaneously because they
    are in the same tag.
    """

    nreviews_tag = tag.find(class_=re.compile(r"^styles_allReviewsHeading"))

    if not nreviews_tag:
        raise RuntimeError(
            "The tag where the score and the number of reviews are hasn't been found."
        )

    nreviews_str = nreviews_tag.get_text()
    match = re.search(r"\(([\d,]+)\)", nreviews_str)

    if not match:
        raise RuntimeError(
            "The number of reviews hasn't been found in the reviews heading."
        )

    # The thousand separator is different for some countries
    nreviews = re.sub(r"[.,\xa0]", "", match.group(1))
    score_tag = tag.find(attrs={"data-rating-typography": "true"})
    score = score_tag.string.replace(",", ".")
    return (int(nreviews), float(score))


def parse_company_v2(tag):
    """Extract the data of a company."""

    nreviews, score = extract_rating_stats_v2(tag)
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
        "rating_distribution": extract_percentage_stars(tag),
    }


def extract_date_experience_v2(tag):
    """
    Extract the date of experience of the review.
    """

    exp_node = tag.find(attrs={"data-testid": "review-badge-date"})

    if not exp_node:
        raise RuntimeError(
            "The tag containing the review's experience date was not found (v2)."
        )

    exp_date_str = concat_strings(exp_node)
    exp_date_str = exp_date_str.split(":")[-1].strip()
    return datetime.datetime.strptime(exp_date_str, "%B %d, %Y")


def extract_is_verified_v2(tag):
    """
    Extract if the review is verified.
    """

    ver_node = tag.find(class_=re.compile(r"^styles_reviewLabels"))
    return bool(ver_node)


def extract_review_info_v2(tag):
    """Extract the review's data"""
    return {
        "author_name": extract_review_author_name_v1(tag),
        "author_id": extract_review_author_id_v1(tag),
        "is_verified": extract_is_verified_v2(tag),
        "star_rating": extract_review_rating_v1(tag),
        "date": extract_review_date_v1(tag),
        "title": extract_review_title_v1(tag),
        "content": extract_review_content_v1(tag),
        "nreviews": extract_number_reviews_author_v1(tag),
        "country": extract_authors_country_v1(tag),
        "date_experience": extract_date_experience_v2(tag),
    }
