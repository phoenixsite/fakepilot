"""
site defines the main operations that enable
the access to the scrapped data.
"""

__docformat__ = 'restructuredtext'

from fakepilot.utils import get_countries
from fakepilot.query import (
    prepare_tquery,
    parse_query)

from fakepilot.xray import get_companies_info, get_reviews

def make_query(query, ncompanies, country, *attrs):

    field_query = parse_query(query)
    string_query = prepare_tquery(field_query)
    return get_companies_info(country, string_query,
                                 field_query, ncompanies, *attrs)

def search(query, ncompanies=25, country="united states",
           with_reviews=False, nreviews=10, *attrs):
    """
    Search for companies with a given query.

    Required attributes in every extracted company can be specified, so
    a company that doesn't cotain any of these attributes will be
    discarded.

    It only returns companies with some score.

    :param query: Query string. It should contain at least one word and
    query clauses can be specified (E.g. 'city: Los Angeles,
    name: Burger').
    :type query: str
    :param ncompanies: Maximum number of companies extracted.
    :type ncompanies: int
    :param country: Country name whose Trustpilot webite is used to
    apply the query.
    :type country: str
    :param with_reviews: Indicates whether the companies reviews are
    extracted.
    :type with_reviews: bool
    :param nreviews: Number of reviews to be extracted. Ignored if with_reviews
    is False.
    :type nreviews: int
    :param attrs: Required attributes for every company.
    :type attrs: list of str
    :rparam: List of extracted data from companies.
    :rtype: list of dict(str, dict)
    """

    if not query:
        raise Exception("A query must be provided.")
    if not country:
        raise Exception(f"A valid country should be provided. The available countries are: {get_countries()}")
    
    companies = make_query(query, ncompanies, country, *attrs)

    if with_reviews:
        for comp_url, company in companies.items():
            company["reviews"] = get_reviews(company["tp_url"], nreviews)

    return companies
