"""Trustpilot scrapping Python package"""

# SPDX-License-Identifier: MIT

import re

from . import xray


def get_reviews(company_page, nreviews):
    """
    Get the reviews' data included in a company's Trustpilot page.

    The number of extracted reviews is the minimum of `nreviews` and
    the number of reviews in the company's page.

    :param company_page: HTML company's page where the reviews are extracted
           from.
    :type company_page: :class:`bs4.BeautifulSoup`
    :param nreviews: Number of reviews to be extracted.
    :type nreviews: int
    :return: Reviews of a company.
    :rtype: list(dict(str,))
    """

    def has_attr_data_service_review_card_paper(tag):
        """
        Check if ``tag`` has the attribute ``'data-service-review-card-paper'``.
        """
        return tag.has_attr("data-service-review-card-paper")

    reviews_section = company_page.find(class_=re.compile("styles_reviewListContainer"))

    # For 2023 pages
    if not reviews_section:
        reviews_section = company_page

    review_tags = reviews_section.find_all(
        has_attr_data_service_review_card_paper, limit=nreviews
    )
    reviews = [xray.extract_review_info(tag) for tag in review_tags]
    return reviews


def extract_info(file, with_reviews=False, nreviews=5):
    """
    Return the information of a company page.

    :param file: Company's page of Trustpilot.
    :type file: file object
    :param with_reviews: Indicates whether the company's reviews are
           extracted.
    :type with_reviews: bool, optional
    :param nreviews: Number of reviews to be extracted. Ignored if `with_reviews`
           is ``False``.
    :type nreviews: int, optional
    :return: Company's information: name (``'name'``), URL (``'url'``),
            number of reviews in Trustpilot (``'nreviews'``),
            score (``'address'``) and if the company's profile is claimed
            (``'is_claimed'``) by the company. The categories, email
            (``'email'``),
            phone number (``'phone'``), address (``'address'``) and
            rating distribution (``'rating_distribution'``) are
            also included if they are on the page. In case of the reviews,
            which are included under the key ``'reviews'``, for each
            one the returned values are the author's name (``'author_name'``),
            the author's id (``'author_id'``)
            in Trustpilot, rating (``'star_rating'``),
            date of publication (``'date'``), the text content
            (``'content'``), the number of reviews made by the author of the
            review (``'nreviews'``), the country that the author is from
            (``'country'``), the date of experience (``'date_experience'``)
            and if the review is verified (``'is_verified'``).
    :rtype: dict(str, )
    """

    company_page = xray.parse_page(file)
    company = xray.extract_company_info(company_page)

    if with_reviews:
        company["reviews"] = get_reviews(company_page, nreviews)

    return company
