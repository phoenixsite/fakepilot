import unittest
from functools import reduce
from fakepilot.query import (
    prepare_tquery,
    parse_query
    )
from fakepilot import (
    search)

class TestSearchQueries(unittest.TestCase):

    def test_plus(self):
        """
        Test the transformation of UTF-8 supported characters to
        valid characters in an url.
        """
        
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
        cs = search(query, country, 5)

        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0].city, 'Almería')
        self.assertEqual(cs[0].country, 'España')

    def test_business_required(self):
        
        country = 'espana'
        query = 'city: almería, country: españa'
        cs = search(query, country, 7, "phone")
        self.assertEqual(len(cs), 7)
        has_phone = reduce(lambda x, y: x and y, [c.phone for c in cs])
        self.assertTrue(has_phone)

        cs = search(query, country, 7, "address")
        self.assertEqual(len(cs), 7)
        has_address = reduce(lambda  x, y: x and y, [c.address for c in cs])
        self.assertTrue(has_address)

        

        
