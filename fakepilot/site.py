import os
import re

import warnings

from bs4 import SoupStrainer
from urllib import request
from urllib.error import HTTPError


from . import _xray as xray, utils


def tp_open_url(url, only_class=None):
    """
    Open a Trustpilot URL and manages the response from the site.

    It checks if the response from Trustpilot indicates that the
    access is forbidden.

    :param url: A Trustpilot URL
    :type url: str
    :param only_class: Limits the construction of the document tree.
    :type only_class: :class:`bs4.SoupStrainer`, optional
    :return: Parsed page.
    :rtype: :class:`bs4.BeautifulSoup`
    :raises RuntimeError: if Trustpilot has forbidden the access to the site.
    """

    req = utils.construct_request(url)
    try:
        with request.urlopen(req) as r:
            parsed_page = xray.parse_page(r, only_class)
    except HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "Forbidden access to Trustpilot. You've made too many " "requests."
            ) from e

        raise e

    return parsed_page


def analyse_result_tag(tag, country):
    """
    Analyse a result tag from the Trustpilot's search page and extract
    the information of the company the tag refers to.

    Return the parsed page if the reviews are required to be
    extracted in following calls.

    :param tag: Result tag from the search page.
    :type tag: :class:`bs4.Tag`
    :param country: Trustpilot's country to search on.
    :type country: str
    :return: Company's data and corresponding parsed HTML.
    :rtype: (dict(str,), :class:`bs4.BeautifulSoup`)
    """

    # Obtain the company's URL in Trustpilot
    company_url = tag.find(href=re.compile("/review/")).get("href")
    tp_comp_url = utils.get_tp_company_url(company_url, country)

    company_page = tp_open_url(tp_comp_url)
    company = xray.extract_company_info(company_page)
    company["tp_url"] = tp_comp_url

    # If the company's website has closed, the tag in the
    # company page where those attributes were supposed to be
    # are not shown, so we provide them from the data shown
    # in the result tag.
    # Example: https://www.trustpilot.com/review/rumbles.dk
    if not (company["score"] and company["nreviews"]):
        (
            company["score"],
            company["nreviews"],
        ) = xray.extract_nreviews_score_search(tag)

    return company, company_page


def get_reviews(company_page, is_local, nreviews, tp_comp_url):
    """
    Get the reviews' data included in a company's Trustpilot page.

    The number of extracted reviews is the minimum of `nreviews` and
    the sum of the number of reviews in each page.

    :param company_page: HTML company's page where the reviews are extracted
           from.
    :type company_page: :class:`bs4.Tag`
    :param is_local: Indicates if `company_page` was obtained from a local
           file or by accessing a Trustpilot page.
    :type is_local: boolean
    :param nreviews: Number of reviews to be extracted.
    :type nreviews: int
    :param tp_comp_url: Trustpilot URL of the company that the reviews are extracted
           from. Ignored if `is_local` is ``True``.
    :type tp_comp_url: str
    :return: Reviews of a company.
    :rtype: list(dict(str,))
    """

    max_npages = xray.get_npages(company_page) if not is_local else 1

    only_reviews = SoupStrainer(class_=xray.REVIEW_CLASS)
    review_tags = company_page.find_all(class_=xray.REVIEW_CLASS, limit=nreviews)
    reviews = [xray.extract_review_info(tag) for tag in review_tags]
    current_page = 2

    # If the source the company_page comes from is a local file, then
    # we don't parse more reviews with thanks to max_length == 1.
    while current_page <= max_npages and len(reviews) < nreviews:

        try:
            parsed_page = tp_open_url(
                utils.get_company_url_paged(tp_comp_url, current_page), only_reviews
            )
        except RuntimeError as e:
            warnings.warn(
                str(e) + " Returning the fecthed the reviews.",
                RuntimeWarning,
            )
            break

        review_tags = parsed_page.find_all(
            class_=xray.REVIEW_CLASS, limit=nreviews - len(reviews)
        )
        reviews.extend([xray.extract_review_info(tag) for tag in review_tags])
        current_page += 1

    return reviews


def search(
    query,
    ncompanies=5,
    with_reviews=False,
    nreviews=5,
    required_attrs=None,
    country="united states",
):
    """
    Return the search results that match a given query.

    It can be specified that every resulting company must have certain
    attributes, so a company that doesn't cotain any of these attributes is
    discarded.

    It only returns companies with some score.

    :param query: Query string. It should contain at least one word.
    :type query: str
    :param ncompanies: Maximum number of companies extracted.
    :type ncompanies: int, optional
    :param with_reviews: Indicates whether the companies' reviews are
           extracted.
    :type with_reviews: bool, optional
    :param nreviews: Number of reviews to be extracted. Ignored if `with_reviews`
           is ``False``.
    :type nreviews: int, optional
    :param required_attrs: Required attributes that every resulting company
           must have. The possible attributes that can be specified are:

           1. ``'email'``
           2. ``'phone'``
           3. ``'address'``

    :type required_attrs: list[str], str or None, optional
    :param country: Country name whose Trustpilot webite is used to
           apply the query. The available countries are:

           1. ``'australia'``
           2. ``'brasil'``
           3. ``'belgie'``
           4. ``'belgique'``
           5. ``'canada'``
           6. ``'danmark'``
           7. ``'deutschland'``
           8. ``'espana'``
           9. ``'france'``
           10. ``'ireland'``
           11. ``'japan'``
           12. ``'nederland'``
           13. ``'new zealand'``
           14. ``'norge'``
           15. ``'osterreich'``
           16. ``'portugal'``
           17. ``'polska'``
           18. ``'schweiz'``
           19. ``'suomi'``
           20. ``'sverige'``
           21. ``'united kingdom'``
           22. ``'united states'``

    :type country: str, optional
    :return: List of extracted data from companies.
             For all the companies its name, URL, Trustpilot URL, score
             and number of reviews.
             Eventually, it may also include its contact phone, email address,
             Trustpilot categories and partial or complete address.
             If an attribute is not extracted, its
             value is None. The extracted URL is not normalized, it
             is the one used in Trustpilot to uniquely identify each business.
             If present, the address always includes the country.
             Sometimes also the city,
             and eventually an unstructured list of address records, such as
             housenumber, street or postal code. For the extracted data of a
             review, see :func:`get_reviews`.
    :rtype: list[dict(str, )]
    :raises ValueError: if `query` is empty or `country` is not between those
        available.
    :raises RuntimeError: if Trustpilot has denied the first access to the
        page. Not raised if the forbidding occur during the extraction
        of the reviews or some companies have been already extracted.

    See also
    --------
    :func:`get_reviews`

    Examples
    --------
    >>> companies = fakepilot.search("burger", 2)
    >>> companies
    [{'name': 'Burger King', 'url': 'www.burgerking.dk',
    'nreviews': 2791, 'score': 1.7, 'categories': ['Restaurant'], 'email':
    None, 'phone': None, 'address': None, 'tp_url':
    'https://us.trustpilot.com//review/www.burgerking.dk?languages=all'},
    'burger-king.de': {'name': 'Burger King', 'url': 'burger-king.de',
    'nreviews': 1645, 'score': 1.6, 'categories': ['Restaurant'], 'email':
    None, 'phone': None, 'address': None, 'tp_url':
    'https://us.trustpilot.com//review/burger-king.de?languages=all'}]
    >>> companies = fakepilot.search("burger", 2, "norge")
    >>> companies
    [{'name': 'Burger King', 'url': 'burgerking.no',
    'nreviews': 62, 'score': 2.1, 'categories': None, 'email': None,
    'phone': None, 'address': None, 'tp_url':
    'https://no.trustpilot.com//review/burgerking.no?languages=all'},
    'burger-bangs.no': {'name': 'Burger Bangs', 'url': 'burger-bangs.no',
    'nreviews': 4, 'score': 4.0, 'categories': ['Fast food-restaurant',
    'Hamburgerrestaurant'], 'email': 'krs@burger-bangs.no', 'phone':
    '40103183', 'address': 'Kristian IVs gate 19,4612,Kristiansand,
    Norway,Norge', 'tp_url':
    'https://no.trustpilot.com//review/burger-bangs.no?languages=all'}]
    >>> companies = fakepilot.search("burger", 1, with_reviews=True, nreviews=1)
    >>> companies
    [{'name': 'Burger King', 'url': 'www.burgerking.dk',
    'nreviews': 2791, 'score': 1.7, 'categories': ['Restaurant'], 'email':
    None, 'phone': None, 'address': None, 'tp_url':
    'https://us.trustpilot.com//review/www.burgerking.dk?languages=all',
    'reviews': [{'author_name': 'Po', 'author_id': '56bd70ff98f61d001203539e',
    'star_rating': 1.0, 'date': datetime.datetime(2024, 1, 1, 17, 41, 57),
    'content': b'Elendig service Null kontroll av ansatte og d\xc3\xa5rlig
    spr\xc3\xa5k forst\xc3\xa5else. V\xc3\xa6rt der mange ganger. F\xc3\xa5r
    feil mat, mangler mat. Mest frustrerende er ventetiden. Flere ganger ventet
    40-45 minutter b\xc3\xa5de inne og ved take away drive in. Drive in er ofte
    treg, tekniske problemer eller at det blir glemt av.'}]}]
    """

    if not query:
        raise ValueError("Query not provided. There must be at least a character.")

    parsed_page = tp_open_url(utils.get_search_url(country, query))
    max_npages = xray.get_npages(parsed_page)
    result_tags = parsed_page.find_all(class_=xray.BUSINESS_CLASS, limit=ncompanies)

    if required_attrs:
        result_tags = [
            tag for tag in result_tags if xray.has_attrs(tag, required_attrs)
        ]

    companies = []
    try:
        for tag in result_tags:
            company, company_page = analyse_result_tag(tag, country)
            if with_reviews:
                company["nreviews"] = get_reviews(
                    company_page, False, nreviews, company["tp_url"]
                )
            companies.append(company)

        current_page = 2

    except RuntimeError as e:
        warnings.warn(
            str(e) + " Returning the fecthed companies.",
            RuntimeWarning,
        )
        current_page = max_npages

    while current_page <= max_npages and len(companies) < ncompanies:

        try:
            search_page = tp_open_url(
                utils.get_search_url(country, query, current_page)
            )
        except RuntimeError as e:
            warnings.warn(
                str(e) + " Returning the fetched companies.",
                RuntimeWarning,
            )
            break

        result_tags = search_page.find_all(
            class_=xray.BUSINESS_CLASS, limit=(ncompanies - len(companies))
        )

        if required_attrs:
            result_tags = [
                tag for tag in result_tags if xray.has_attrs(tag, required_attrs)
            ]

        try:
            for tag in result_tags:
                company, company_page = analyse_result_tag(
                    tag, with_reviews, nreviews, country
                )
                if with_reviews:
                    company["nreviews"] = get_reviews(
                        company_page, False, nreviews, company["tp_url"]
                    )

                companies.append(company)

        except RuntimeError as e:
            warnings.warn(
                str(e) + " Returning the fecthed companies.",
                RuntimeWarning,
            )
            break

        current_page += 1

    return companies


def get_company(source, with_reviews=False, nreviews=5, country="united states"):
    """
    Return the information of just one company.

    :param source: URL to a company's Trustpilot page or path-like object.
    :type source: str
    :param with_reviews: Indicates whether the company's reviews are
           extracted.
    :type with_reviews: bool, optional
    :param nreviews: Number of reviews to be extracted. Ignored if `with_reviews`
           is ``False``.
    :type nreviews: int, optional
    :param country: Country name whose Trustpilot webite is used to
           apply the query. To see all the available countries see :func:`search`.
           Ignored if `source` is a path-like object.
    :type country: str, optional
    :return: Company's information
    :rtype: dict(str, )
    :raises RuntimeError: if the source is a URL and Trustpilot has denied
        the first access to the page. Not raised if the forbidding occur
        during the extraction of the reviews.
    """

    is_local = os.path.isfile(source)

    if not is_local:
        company_page = tp_open_url(source)
    else:
        with open(source, encoding="utf8") as f:
            company_page = xray.parse_page(f, None)

    company = xray.extract_company_info(company_page)
    company["tp_url"] = utils.get_tp_company_url(company["url"], country)

    if with_reviews:
        company["reviews"] = get_reviews(
            company_page, is_local, nreviews, company["tp_url"]
        )

    return company
