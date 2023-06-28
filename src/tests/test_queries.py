import unittest
from fakepilot.query import (
    prepare_tquery,
    parse_query
    )
from fakepilot import (
    search)

class TestSearchQueries(unittest.TestCase):

    def test_plus(self):
        field_query = {
            'city': 'Málaga',
            'country': 'España',
            'name': 'Sol y playa'}
        results = 'M%C3%A1laga+Sol+y+playa'
        self.assertEqual(prepare_tquery(field_query), results)

    def test_parse_query(self):
        query = 'city:Madrid, country:España'
        result = {'city': 'Madrid', 'country': 'España'}
        self.assertEqual(parse_query(query), result)

        query = 'city: Madrid, country: España'
        self.assertEqual(parse_query(query), result)

        query = 'calzados pasitos'
        result = {'general': 'calzados pasitos'}
        self.assertEqual(parse_query(query), result)

        query = 'name: calzados pasitos'
        result = {'name': 'calzados pasitos'}
        self.assertEqual(parse_query(query), result)

        query = 'country: España, city:Madrid, name: Burger'
        result = {
            'city': 'Madrid',
            'country': 'España',
            'name': 'Burger'}
        self.assertEqual(parse_query(query), result)

    def test_business(self):

        country = 'espana'
        query = 'city: almería, country: españa'
        query += ', name: anglophone'
        businesses = search(query, country, 5)
        print(len(businesses))
        for business in businesses:
            business.extract_reviews(3)
            print(business)
            print("\n")

    def test_business_required(self):
        
        country = 'espana'
        query = 'city: almería, country: españa'
        businesses = search(query, country, 7, "phone")
        for business in businesses:
            business.extract_reviews(3)
            print(business)
            print("\n")
