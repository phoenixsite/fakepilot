"""Trustpilot scrapping Python package"""

# SPDX-License-Identifier: MIT

import re

from . import xray

REVIEW_CLASS = re.compile("styles_reviewCardInner")


def get_reviews(company_page, nreviews):
    """
    Get the reviews' data included in a company's Trustpilot page.

    The number of extracted reviews is the minimum of `nreviews` and
    the number of reviews in the company's page.

    :param company_page: HTML company's page where the reviews are extracted
           from.
    :type company_page: :class:`bs4.Tag`
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


def extract_info(source, with_reviews=False, nreviews=5):
    """
    Return the information of a company page.

    :param source: Company's page of Trustpilot.
    :type source: file-like
    :param with_reviews: Indicates whether the company's reviews are
           extracted.
    :type with_reviews: bool, optional
    :param nreviews: Number of reviews to be extracted. Ignored if `with_reviews`
           is ``False``.
    :type nreviews: int, optional
    :return: Company's information
    :rtype: dict(str, )
    """

    with open(source, encoding="utf8") as f:
        company_page = xray.parse_page(f)

    company = xray.extract_company_info(company_page)

    if with_reviews:
        company["reviews"] = get_reviews(company_page, nreviews)

    return company
