
import urllib.request as request
import unittest
from fakepilot._xray import get_npages, get_companies_info, CompanyDoc
from bs4 import BeautifulSoup

PARSER = 'html.parser'

class TestXray(unittest.TestCase):

    def setUp(self):

        self.urls = [
            'https://www.trustpilot.com/review/beautytheshop.com?languages=all',
            'https://www.trustpilot.com/review/www.granada.no?languages=all',
            'https://www.trustpilot.com/review/djmania.es?languages=all',
            'https://www.trustpilot.com/review/www.burgerking.dk?languages=all',
            'https://www.trustpilot.com/review/burgerking.no?languages=all',
            'https://www.trustpilot.com/review/www.burgerking.fr?languages=all',
            'https://www.trustpilot.com/review/twenix.es?languages=all',
            'https://www.trustpilot.com/review/elejidoshopping.es?languages=all'
        ]

        # Data of 2023-12-28
        self.solutions = {
            "names": [
                "BeautyTheShop",
                "Granada AS",
                "DJMania.es",
                "Burger King",
                "Burger King",
                "BURGER KING FRANCE",
                "Twenix",
                "elejidoshopping",
            ],
            "rating_stats": [
                (2755, 4.4),
                (1, 3.7),
                (46, 2.3),
                (2782, 1.7),
                (59, 2.2),
                (565, 2.6),
                (48, 4.1),
                (21, 2.5),
            ],
            "categories": [
                ["Cosmetics and Perfumes Supplier",
                 "Cosmetics Store",
                 "Perfume Store"
                 ],
                ["Business Administration Service",
                 "e-Commerce Service",
                 "Logistics Service",
                 "Online Marketplace",
                 "Translator",
                 "Warehouse"],
                ["e-Commerce Service"],
                ["Restaurant"],
                None,
                ["Restaurants & Bars"],
                ["Educational Institution"],
                None
            ],
            "npages": [130, 1, 3, 136, 3, 27, 3, 1],
        }

        search_data = {"score": -1, "nreviews": -1}
        self.cdocs = [CompanyDoc(request.urlopen(url), PARSER, search_data)
                              for url in self.urls]

    def test_extract_name(self):

        for i, r in enumerate(self.cdocs):
            name = r.extract_name()
            with self.subTest(url=self.urls[i]):
                self.assertEqual(name, self.solutions["names"][i])
        
    def test_extract_rating_stats(self):

        for i, r in enumerate(self.cdocs):
            nreviews = r.extract_nreviews()
            score = r.extract_score()
            with self.subTest(url=self.urls[i]):
                self.assertEqual((nreviews, score), self.solutions["rating_stats"][i])
        
    def test_extract_categories(self):
        """
        Test that the categories extracted from a company are the correct ones
        for some example companies.
        """
        
        for i, r in enumerate(self.cdocs):
            categories = r.extract_categories()
            with self.subTest(url=self.urls[i]):
                self.assertEqual(categories, self.solutions["categories"][i])
        
    def test_getnpages(self):
        """
        Test that the number of pages extracted is correct.
        """
        
        for i, r in enumerate(self.cdocs):
            npages = get_npages(r)
            with self.subTest(url=self.urls[i]):
                self.assertEqual(npages, self.solutions["npages"][i])

    def test_number_companies(self):
        """
        Test that the number of companies extracted is correct.
        """
        
        string_query = 'granada'
        country = "Espana"
        nbusinesses = [2, 5, 10]

        for nbusiness in nbusinesses:
            urls = get_companies_info(country, string_query, {}, nbusiness, None)
            self.assertEqual(nbusiness, len(urls))
