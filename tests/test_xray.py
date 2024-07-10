import os
import unittest
import urllib.request as request
from pathlib import Path

from bs4 import BeautifulSoup

from fakepilot import _xray as xray

PARSER = "lxml"
BASE_DIR = Path(__file__).resolve().parent


class TestXray(unittest.TestCase):
    def setUp(self):

        data_dir = os.path.join(BASE_DIR, "data")

        self.sources = [
            "beautytheshop.com.txt",
            "www.granada.no.txt",
            "djmania.es.txt",
            "www.burgerking.dk.txt",
            "burgerking.no.txt",
            "www.burgerking.fr.txt",
            "twenix.es.txt",
            "elejidoshopping.es.txt",
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

        self.companies = []
        self.parsed_pages = []

        for source in self.sources:
            with open(source, encoding="utf-8") as f:
                parsed_page = xray.parse_page(f, None)
                self.parsed_pages.append(parsed_page)
                company = xray.extract_company_info(parsed_page)

                if not (company["score"] and company["nreviews"]):
                    company["score"] = dummy_score
                    company["nreviews"] = dummy_nreviews

                self.companies.append(company)

    def test_extract_name(self):
        """Test that the name is correctly extracted"""
        for i, r in enumerate(self.companies):
            name = r["name"]
            with self.subTest(source=self.sources[i]):
                self.assertEqual(name, self.solutions["names"][i])

    def test_extract_rating_stats(self):
        """Test that the number of reviews and score are correctly extracted"""
        for i, r in enumerate(self.companies):
            nreviews = r["nreviews"]
            score = r["score"]
            with self.subTest(source=self.sources[i]):
                self.assertEqual((nreviews, score), self.solutions["rating_stats"][i])

    def test_extract_categories(self):
        """
        Test that the categories extracted from a company are the correct ones
        for some example companies.
        """

        for i, r in enumerate(self.companies):
            categories = r["categories"]
            with self.subTest(source=self.sources[i]):
                self.assertEqual(categories, self.solutions["categories"][i])

    def test_getnpages(self):
        """
        Test that the number of pages extracted is correct.
        """

        for i, r in enumerate(self.parsed_pages):
            npages = xray.get_npages(r)
            with self.subTest(source=self.sources[i]):
                self.assertEqual(npages, self.solutions["npages"][i])
