"""
This module defines how the data is scrapped from the Trustpilot site.
"""

import os
import re
import warnings
from datetime import datetime
from functools import cached_property
from urllib import request
from urllib.parse import parse_qs, urlparse
from urllib.error import HTTPError

from bs4 import BeautifulSoup, SoupStrainer

from . import utils

PARSER = "lxml"
REVIEW_CLASS = re.compile("styles_reviewCardInner")
BUSINESS_CLASS = re.compile("businessUnitResult")


# Used to speed up the BeautifulSoup detection of the markup encoding
TPENCODING = "utf-8"


def has_attrs(tag, attrs):
    """
    Check that a company has registered on Trustpilot some attributes`.

    :param tag: HTML tag that should contain SVG icons.
    :type tag: :ref:`bs4:Tag`
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
    :type tag: :ref:`bs4:Tag`
    :return: Number of reviews and Trustscore of a company.
    :rtype: tuple(float, int)
    """

    rating_tag = tag.find(class_=re.compile("ratingText"))
    mini_box = list(rating_tag.stripped_strings)
    return (mini_box[1], mini_box[3])


class CompanyDoc(BeautifulSoup):
    """
    Represents the HTML page of a company as a BeautifulSoup data
    structure.

    It is used to avoid double checkings when restrictions over the
    attributes of a company are imposed. Also, multiple attributes are
    included in the same tag, so when one of them is extracted
    the other is got as well.  When an attribute is
    extracted for the first time, then it is
    saved in the object so following extractions doesn't need to get into
    the HTML tree again.

    :param markup: HTML page that contains the information of a business.
    :type markup: http.client.HTTPResponse or str
    :param parser: BeautifulSoup parser. The lmxml parser is used.
                   See :ref:`bs4:parser-installation`.
    :type parser: str
    :param search_data: Company data extracted from the search page.
    :type search_data: dict(str,)
    """

    def __init__(self, markup, parser, score, nreviews):
        BeautifulSoup.__init__(self, markup, parser, from_encoding=TPENCODING)

        if not score or not nreviews:
            raise ValueError("A value for score and nreviews must be provided")

        self._nreviews = nreviews
        self._score = score
        self._email = None
        self._address = None
        self._phone = None

    @cached_property
    def url(self):
        """
        Return the URL of the company.

        Trustpilot uses the company registered URL to uniquely identify
        a company. However, they aren't normalized. Sometimes they can be
        ``www.company-site.es`` or ``company-site.es``. The URL is returned
        as it is on Trustpilot.
        """

        business_url = self.find(class_=re.compile("styles_websiteUrl"))
        return "".join(business_url.strings)

    @cached_property
    def company_name(self):
        """Return the name of the company."""
        name_tag = self.find("h1", class_=re.compile("title_title"))
        return next(name_tag.find(class_=re.compile("title_displayName")).strings)

    def _extract_rating_stats(self):
        """
        Extract the number of reviews and the TrustScore.

        Both attributes are extracted simultaneously because they
        are in the same tag.
        """

        nreviews_tag = self.find(attrs={"data-reviews-count-typography": "true"})

        if nreviews_tag:
            nreviews = (
                nreviews_tag.string.split()[0]
                if nreviews_tag.string
                else next(nreviews_tag.strings)
            )

            # The thousand separator is different for some countries
            nreviews = re.sub(r"[.,\xa0]", "", nreviews)
            score_tag = self.find(attrs={"data-rating-typography": "true"})
            score = score_tag.string.replace(",", ".")

            self._nreviews = int(nreviews)
            self._score = float(score)

    @property
    def nreviews(self):
        """Return the number of reviews."""
        self._extract_rating_stats()
        return self._nreviews

    @property
    def score(self):
        """Return the TrustScore."""
        self._extract_rating_stats()
        return self._score

    def _extract_contact_info(self):
        """Extract the phone, address and email fields."""

        def is_side_column(css_class):
            return (
                css_class is not None
                and "styles_sideColumnCard" in css_class
                and "paper_paper" in css_class
            )

        info_tag = self.find(class_=is_side_column)

        # The three fields are grouped in the same 'address' tag
        address_tag = info_tag.find("address")
        parsed_data = {"phone": None, "email": None, "address": None}

        if address_tag:

            # As the address field does not have a specific structure,
            # the other two are searched and the last one would the
            # address field
            reg_fields = [
                ("phone", re.compile(r"^\+?\d[\d-]+")),
                (
                    "email",
                    re.compile(
                        r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
                    ),
                ),
            ]
            contact_elements = address_tag.findAll(
                "li", class_=re.compile("styles_contactInfoElement")
            )

            for contact_info in contact_elements:

                line = ",".join(contact_info.strings)
                field, count = None, 0

                while not field and count < len(reg_fields):

                    if reg_fields[count][1].search(line):
                        field = reg_fields[count][0]

                    count += 1

                if not field:
                    field = "address"

                parsed_data[field] = line

            self._email = parsed_data["email"]
            self._phone = parsed_data["phone"]
            self._address = parsed_data["address"]

    @property
    def email(self):
        """Return the company's contact email address."""
        self._extract_contact_info()
        return self._email

    @property
    def phone(self):
        """Return the company's contact phone number."""
        self._extract_contact_info()
        return self._phone

    @property
    def address(self):
        """Return the company's address."""
        self._extract_contact_info()
        return self._address

    @cached_property
    def categories(self):
        """Return the company's category list."""
        cat_section = self.find(class_=re.compile("styles_categoriesList"))
        categories = None

        if cat_section:
            cat_refs = cat_section.findAll(href=re.compile("/categories/"))
            categories = [cat_tag.string for cat_tag in cat_refs]

        return categories


def get_npages(tag):
    """
    Get the number of pages from the search's result page.

    :param tag: HTML tag of a result-like page.
    :type tag: :ref:`bs4:Tag`
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


def get_company_info(result_tag, country):
    """Extract the data of a company."""
    company_url = result_tag.find(href=re.compile("/review/")).get("href")

    # The number of reviews and TrustScore is passed to CompanyDoc
    # in case the company's website has closed, so the tag in the
    # company page where those attributes were supposed to be
    # are not shown.
    # Example: https://www.trustpilot.com/review/rumbles.dk
    score, nreviews = extract_nreviews_score_search(result_tag)
    tp_comp_url = utils.get_tp_company_url(country, company_url)

    try:
        with request.urlopen(tp_comp_url) as r:
            comp_page = CompanyDoc(r, PARSER, score, nreviews)
    except HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "Forbidden access to Trustpilot. You've made too much"
                "requests tom o Trustpilot."
            ) from e

        raise e

    return {
        "name": comp_page.company_name,
        "url": comp_page.url,
        "nreviews": comp_page.nreviews,
        "score": comp_page.score,
        "categories": comp_page.categories,
        "email": comp_page.email,
        "phone": comp_page.phone,
        "address": comp_page.address,
        "tp_url": tp_comp_url,
    }


def tp_open_url(req):
    """
    Open a Trustpilot URL and manages the response from the site.

    It checks if the response from Trustpilot indicates that the
    access is forbidden.

    :param req: Request that will be sent.
    :type req: request.Request
    :return: Parsed page.
    :rtype: :ref:`bs4:BeautifulSoup`
    """

    try:
        with request.urlopen(req) as r:
            parsed_page = BeautifulSoup(r, PARSER, from_encoding=TPENCODING)
    except HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "Forbidden access to Trustpilot. You've made too many "
                "requests. No results have been fetched."
            ) from e

        raise e

    return parsed_page


def construct_request(url):
    """Construct a request for the given url."""
    # Artificial header. TODO: Random generation of headers and
    # inter-request time.
    hdr = {
        "User-Agent": """Mozilla/5.0 (Windows NT 10.0; Win64; x64;
            rv:102.0) Gecko/20100101 Firefox/102.0"""
    }
    return request.Request(url, headers=hdr)


def get_companies_info(country, query, nbusiness, required_attrs):
    """
    Get the Trustpilot data of the companies that match a query.

    The number of extracted companies is the minimum of `nbusiness` and
    the sum of the number of businesses of each result page.

    :param country: Country whose Trustpilot page is used to scrape.
    :type country: str
    :param query: Query string.
    :type query: str
    :param required_attrs: Required attributes found in a company.
           If a company does not include any of the ones in
           required_attrs, it is discarded.
    :type required_attrs: list[str] or str or None
    :return: Trustpilot companies that match the query.
    :rtype: list[dict(str,)]
    """

    only_results = SoupStrainer(class_=BUSINESS_CLASS)
    req = construct_request(utils.get_search_url(country, query))

    parsed_page = tp_open_url(req)
    max_npages = get_npages(parsed_page)
    result_tags = parsed_page.find_all(class_=BUSINESS_CLASS, limit=nbusiness)

    if required_attrs:
        result_tags = [tag for tag in result_tags if has_attrs(tag, required_attrs)]

    companies = [get_company_info(tag, country) for tag in result_tags]
    current_page = 2

    while current_page <= max_npages and len(companies) < nbusiness:

        req.full_url = utils.get_search_url(country, query, current_page)

        try:
            with request.urlopen(req) as r:
                search_page = BeautifulSoup(
                    r,
                    PARSER,
                    from_encoding=TPENCODING,
                    parse_only=only_results,
                )
        except HTTPError as e:
            if e.code == 403:
                warnings.warn(
                    "Forbidden access to Trustpilot. You've made too many "
                    "requests. Returning the fecthed companies.",
                    RuntimeWarning,
                )
                break

            raise e

        result_tags = search_page.find_all(
            class_=BUSINESS_CLASS, limit=(nbusiness - len(companies))
        )

        if required_attrs:
            result_tags = [tag for tag in result_tags if has_attrs(tag, required_attrs)]

        try:
            for tag in result_tags:
                companies.append(get_company_info(tag, country))
        except HTTPError as e:
            if e.code == 403:
                warnings.warn(
                    "Forbidden access to Trustpilot. You've made too many "
                    "requests to Trustpilot. Returning the fecthed companies.",
                    RuntimeWarning,
                )
                break

            raise e

        current_page += 1

    return companies


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
        raise ValueError("""The tag where the review's date should be isn't present.""")

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


def get_review_info(tag):
    """Extract the review's data"""
    return {
        "author_name": extract_author_name(tag),
        "author_id": extract_author_id(tag),
        "star_rating": extract_rating(tag),
        "date": extract_date(tag),
        "content": extract_content(tag),
    }


def extract_reviews(source, nreviews):
    """
    Extract the reviews' data included in a company's Trustpilot page.

    The number of extracted reviews is the minimum of `nreviews` and
    the sum of the number of reviews in each page.

    If the source is a static local HTML page, then just that page
    is analyzed.

    :param source: URL or path to file from where the data is extracted. If
           it is an URL, then it must be the company's URL on Trustpilot,
           which is like `` https://www.trustpilot.com/review/example-comp``.
    :type source: str or path-like object
    :param nreviews: Number of reviews to be extracted.
    :type nreviews: int
    :return: List of each review's data.
    :rtype: list[dict(str,]
    """

    only_reviews = SoupStrainer(class_=REVIEW_CLASS)

    if os.path.isfile(source):
        is_local = True
        with open(source) as f:
            parsed_page = BeautifulSoup(f, PARSER, from_encoding=TPENCODING)
    else:
        is_local = False
        parsed_page = tp_open_url(source)

    max_npages = get_npages(parsed_page) if not is_local else 1
    review_tags = parsed_page.find_all(class_=REVIEW_CLASS, limit=nreviews)
    reviews = [get_review_info(tag) for tag in review_tags]
    current_page = 2

    while current_page <= max_npages and len(reviews) < nreviews:

        try:
            with request.urlopen(
                utils.get_company_url_paged(source, current_page)
            ) as r:
                parsed_page = BeautifulSoup(
                    r, PARSER, from_encoding=TPENCODING, parse_only=only_reviews
                )
        except HTTPError as e:
            if e.code == 403:
                warnings.warn(
                    "Forbidden access to Trustpilot. You've made too many "
                    "requests. Returning the fecthed the reviews.",
                    RuntimeWarning,
                )
                break

            raise e

        review_tags = parsed_page.find_all(
            class_=REVIEW_CLASS, limit=nreviews - len(reviews)
        )
        reviews.extend([get_review_info(tag) for tag in review_tags])
        current_page += 1

    return reviews
