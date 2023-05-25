import unittest
from fakepilot.xray import (
    get_npages
    )

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
        
            
