from urllib.parse import quote_plus

def prepare_tquery(field_query):
    """
    Transform the queries for each field so it is compatible with the
    search pattern used in a Trustpilot URL

    If city is included, then the country is not included in the query
    string. If country value is included, the city value would loose
    relevance and a lot of business from other cities woulb be extracted.
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

    if not query:
        raise Exception("A query cannot be empty.")

    field_value = {}
    
    if EQ in query:

        search_clauses = query.split(SEP)

        for clause in search_clauses:

            field, value = clause.split(EQ)
            field, value = field.strip(), value.strip()

            if field not in SEARCH_FIELDS:
                raise Exception(f"Searched for {field}. The only fields that can be searched for are {', '.join(SEARCH_FIELDS)}")
            if field in field_value:
                raise Exception("A field cannot be doubled-searched in the same query.")

            field_value[field] = value

        if 'city' in field_value:
            if 'country' not in field_value:
                raise Exception("""If the search is restricted to city,
                then the country of the city must be included as well.""")
    else:
        field_value['general'] = query

    return field_value
            
    
