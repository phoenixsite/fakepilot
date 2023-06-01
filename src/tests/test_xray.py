import unittest
from fakepilot.xray import (
    get_npages,
    find_business_nodes,
    find_review_nodes,
    extract_name,
    extract_rating_stats,
    extract_contact_info
    )

from fakepilot.utils import get_url

from bs4 import BeautifulSoup
import urllib.request as request

PARSER = 'html.parser'

class TestXray(unittest.TestCase):

    def test_extract_name(self):

        urls = ['https://www.trustpilot.com/review/beautytheshop.com',
                'https://www.trustpilot.com/review/www.granada.no']
        solutions = ['BeautyTheShop', 'Granada AS']

        rs = [BeautifulSoup(request.urlopen(url), PARSER) for url in urls]
        names = [extract_name(r) for r in rs]
        self.assertEqual(names, solutions)
        
    def test_extract_rating_stats(self):

        urls = ['https://www.trustpilot.com/review/realpublicidad.com',
                'https://www.trustpilot.com/review/www.hsnstore.com']

        solutions = [(0, 0), (17173, 4.6)]
        rs = [BeautifulSoup(request.urlopen(url), PARSER) for url in urls]
        results = [extract_rating_stats(r) for r in rs]
        self.assertEqual(solutions, results)

    def test_extract_contact_info(self):

        urls = ['https://www.trustpilot.com/review/beautytheshop.com',
                'https://www.trustpilot.com/review/www.granada.no',
                'https://www.trustpilot.com/review/djmania.es',
                'https://www.trustpilot.com/review/www.burgerking.dk',
                'https://www.trustpilot.com/review/burgerking.no',
                'https://www.trustpilot.com/review/www.burgerking.fr'
                ]

        rs = [BeautifulSoup(request.urlopen(url), PARSER) for url in urls]

        for r in rs:
            contact_data = extract_contact_info(r)
            for k in contact_data:
                print(f"{k}: {contact_data[k]}")
            print("------")
        
        
    def test_getnpages(self):

        urls = [
            'https://es.trustpilot.com/review/hideout-burger.com?languages=all',
            'https://es.trustpilot.com/review/twenix.es?languages=all',
            'https://es.trustpilot.com/review/anglophone.es',
            'https://es.trustpilot.com/review/granadamaison.com',
            'https://es.trustpilot.com/review/plata925.com',
            'https://es.trustpilot.com/review/vibenglish.com',
            'https://es.trustpilot.com/review/burger-king.de?languages=all']
        
        # Results as 2023-05-23
        solutions = [1, 2, 3, 5, 6, 6, 71]
        parsed_pages = [BeautifulSoup(request.urlopen(url), PARSER) for url in urls]
        results = [get_npages(page) for page in parsed_pages]
        self.assertEqual(results, solutions)

    def test_find_business_nodes(self):

        string_query = 'granada'
        url = get_url("Espana")
        nbusinesses = [2, 5, 10, 13, 25, 50]

        for nbusiness in nbusinesses:
            nodes = find_business_nodes(url, string_query, {}, nbusiness)
            self.assertEqual(nbusiness, len(nodes))
        
    def test_find_review_nodes(self):

        url = 'https://es.trustpilot.com/review/www.hsnstore.com?languages=all'
        nreviews = [1, 2, 5, 15, 30, 50]

        for nreview in nreviews:
            nodes = find_review_nodes(url, nreview)
            self.assertEqual(nreview, len(nodes))
