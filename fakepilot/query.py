"""
Defines the methods and functions to parse and transform queries.
"""

from urllib.parse import quote_plus

def prepare_tquery(field_query):
    """
    Transform the queries for each field so it is compatible with the
    search pattern used in a Trustpilot URL

    If the city clause is included, then the country one is not, as
    the city field value would loose relevance in the query and a
    lot of business from other cities would be extracted.
    """

    if 'city' in field_query:
        query = quote_plus(field_query['city'])
    if 'name' in field_query:
        query += quote_plus(f" {field_query['name']}")
    if 'general' in field_query:
        query = quote_plus(field_query['general'])

    return query

SEARCH_FIELDS = ['city', 'country', 'name']
SEP = ','
EQ = ':'

def parse_query(query):
    """
    Parse a query string given as a string argument. 
    """

    if not query:
        raise ValueError("A query cannot be empty.")

    field_value = {}

    if EQ in query:

        search_clauses = query.split(SEP)

        for clause in search_clauses:

            field, value = clause.split(EQ)
            field, value = field.strip(), value.strip()

            if field not in SEARCH_FIELDS:
                raise ValueError("Searched for {field}. The only fields that can be"\
                f"searched for are {', '.join(SEARCH_FIELDS)}")
            if field in field_value:
                raise ValueError("A field cannot be doubled-searched in the same query.")

            field_value[field] = value

        if 'city' in field_value:
            if 'country' not in field_value:
                raise ValueError("""If the search is restricted to city,
                then the country of the city must be included as well.""")
    else:
        field_value['general'] = query

    return field_value
