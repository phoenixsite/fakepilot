import unittest
from fakepilot.xray import (
    get_npages,
    get_companies_info,
    get_reviews,
    CompanyDoc
    )

from bs4 import BeautifulSoup
import urllib.request as request

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

        self.cdocs = [CompanyDoc(request.urlopen(url), PARSER)
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
        Tests that the categories extracted from a company are the correct ones
        for some example companies.
        """
        
        for i, r in enumerate(self.cdocs):
            categories = r.extract_categories()
            with self.subTest(url=self.urls[i]):
                self.assertEqual(categories, self.solutions["categories"][i])
        
    def test_getnpages(self):
        """
        Tests that the number of pages extracted from a reviews company page is correct
        for some example companies.
        """
        
        for i, r in enumerate(self.cdocs):
            npages = get_npages(r)
            with self.subTest(url=self.urls[i]):
                self.assertEqual(npages, self.solutions["npages"][i])

    def test_number_companies(self):
        """
        Tests that the number of companies extracted is correct for an example
        query.
        """
        
        string_query = 'granada'
        country = "Espana"
        nbusinesses = [2, 5, 10, 13, 25, 50]

        for nbusiness in nbusinesses:
            urls = get_companies_info(country, string_query, {}, nbusiness)
            self.assertEqual(nbusiness, len(urls))
        
    def test_number_reviews(self):
        """Tests that the number of reviews extracted is correct."""

        url = 'https://es.trustpilot.com/review/www.hsnstore.com?languages=all'
        nreviews = [1, 2, 5, 15, 30, 50]

        for nreview in nreviews:
            reviews = get_reviews(url, nreview)
            with self.subTest(nreviews=nreview):
                self.assertEqual(nreview, len(reviews))
