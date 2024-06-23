import os
import unittest
import urllib.request as request
from pathlib import Path

from bs4 import BeautifulSoup

from fakepilot._xray import CompanyDoc, get_companies_info, get_npages

PARSER = "lxml"
BASE_DIR = Path(__file__).resolve().parent


class TestXray(unittest.TestCase):
    def setUp(self):

        data_dir = os.path.join(BASE_DIR, "data")

        self.sources = [
            "beautytheshop.com.htm",
            "www.granada.no.htm",
            "djmania.es.htm",
            "www.burgerking.dk.htm",
            "burgerking.no.htm",
            "www.burgerking.fr.htm",
            "twenix.es.htm",
            "elejidoshopping.es.htm",
        ]

        self.sources = [os.path.join(data_dir, source) for source in self.sources]

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
                (2989, 4.4),
                (1, 3.7),
                (52, 2.3),
                (3205, 1.9),
                (99, 2.3),
                (775, 3.1),
                (85, 4.4),
                (21, 2.5),
            ],
            "categories": [
                ["Cosmetics and Perfumes Supplier", "Cosmetics Store", "Perfume Store"],
                [
                    "Business Administration Service",
                    "e-Commerce Service",
                    "Logistics Service",
                    "Online Marketplace",
                    "Translator",
                    "Warehouse",
                ],
                ["e-Commerce Service"],
                ["Restaurant"],
                None,
                ["Restaurants & Bars"],
                ["Educational Institution"],
                None,
            ],
            "npages": [141, 1, 3, 156, 5, 38, 4, 2],
        }

        # Dummy search_data. Because the tests pages are not
        # extracted from the search's result page, we cannot
        # extract from there the score and nreviews from that
        # page, so we provide dummy data
        dummy_score = 2.5
        dummy_nreviews = 21

        self.cdocs = []
        for source in self.sources:
            with open(source, encoding="utf-8") as f:
                self.cdocs.append(
                    CompanyDoc(f.read(), PARSER, dummy_score, dummy_nreviews)
                )

    def test_extract_name(self):
        """Test that the name is correctly extracted"""
        for i, r in enumerate(self.cdocs):
            name = r.company_name
            with self.subTest(source=self.sources[i]):
                self.assertEqual(name, self.solutions["names"][i])

    def test_extract_rating_stats(self):
        """Test that the number of reviews and score are correctly extracted"""
        for i, r in enumerate(self.cdocs):
            nreviews = r.nreviews
            score = r.score
            with self.subTest(source=self.sources[i]):
                self.assertEqual((nreviews, score), self.solutions["rating_stats"][i])

    def test_extract_categories(self):
        """
        Test that the categories extracted from a company are the correct ones
        for some example companies.
        """

        for i, r in enumerate(self.cdocs):
            categories = r.categories
            with self.subTest(source=self.sources[i]):
                self.assertEqual(categories, self.solutions["categories"][i])

    def test_getnpages(self):
        """
        Test that the number of pages extracted is correct.
        """

        for i, r in enumerate(self.cdocs):
            npages = get_npages(r)
            with self.subTest(source=self.sources[i]):
                self.assertEqual(npages, self.solutions["npages"][i])

    def test_number_companies(self):
        """
        Test that the number of companies extracted is correct.
        """

        string_query = "granada"
        country = "Espana"
        nbusinesses = [2, 5, 10]

        for nbusiness in nbusinesses:
            urls = get_companies_info(country, string_query, nbusiness, None)
            self.assertEqual(nbusiness, len(urls))
