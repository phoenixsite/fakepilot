"""
Defines the main operations that enable the access to the scrapped data.
"""

import os
from urllib import request
from .utils import COUNTRIES
from .query import prepare_tquery, parse_query
from ._xray import get_companies_info, extract_reviews

def search(query, ncompanies=10, country="united states",
           with_reviews=False, nreviews=5, required_attrs=None):
    """
    Return the search results that match a given query.

    It can be specified that every resulting company must have certain
    attributes, so a company that doesn't cotain any of these attributes is
    discarded.

    It only returns companies with some score.

    :param query: Query string. It should contain at least one word and
           query clauses can be specified, e.g, ``'city: Los Angeles,
           name: Burger'``.
    :type query: str
    :param ncompanies: Maximum number of resulting companies.
    :type ncompanies: int, optional
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
    :param with_reviews: Indicates whether the companies reviews are
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
    :return: List of extracted data from companies.
             For all the companies its name, URL,
             score and number of reviews.
             Eventually, they may also include its contact phone, email address,
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
    :raise ValueError: if query is empty or country is not between those
           available.

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
        raise ValueError("A query must be provided.")
    if not country:

        all_countries = [country.title() for country in COUNTRIES.keys()]
        s = ", ".join(all_countries[:len(all_countries) - 1])
        s = f"{s} and {all_countries[-1]}"
        raise ValueError("""A valid country should be provided. The"""
                         f"available countries are: {s}")

    field_query = parse_query(query)
    string_query = prepare_tquery(field_query)
    companies = get_companies_info(country, string_query,
                                 field_query, ncompanies, required_attrs)

    if with_reviews:
        for company in companies:
            company["reviews"] = get_reviews(company["tp_url"], nreviews)

    return companies


def get_reviews(source, nreviews):
    """
    Get the reviews given by `source`.

    :param source: URL or path to file from where the data is extracted.
    :type source: str or path-like object
    :param nreviews: Number of reviews to be extracted.
    :type nreviews: int
    :return: List of each reviews' data.
    :rtype: list[dict(str,)]
    """

    is_local, url = True, None

    if os.path.isfile(source):
        with open(source, encoding="utf-8") as f:
            html_tag = f.read()
    else:
        with request.urlopen(source) as r:
            html_tag = r.read()

        is_local = False
        url = source

    return extract_reviews(html_tag, nreviews, is_local, url)
