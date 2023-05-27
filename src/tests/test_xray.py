import unittest
from fakepilot.xray import (
    get_npages,
    find_business_nodes,
    find_review_nodes
    )

from fakepilot.utils import get_url

from bs4 import BeautifulSoup
import urllib.request as request

PARSER = 'lxml'

class TestXray(unittest.TestCase):

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
