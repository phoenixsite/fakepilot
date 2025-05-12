""" """

# SPDX-License-Identifier: MIT

import os
import unittest
from pathlib import Path

from fakepilot import _xray as xray
from fakepilot.site import get_reviews

PARSER = "lxml"
BASE_DIR = Path(__file__).resolve().parent


class TestXray(unittest.TestCase):
    def setUp(self):

        data_dir = os.path.join(BASE_DIR, "data")

        # Data of 2023-12-28

        self.data = {
            "beautytheshop.com.txt": {
                "name": "BeautyTheShop",
                "rating_stats": (2989, 4.4),
                "categories": [
                    "Cosmetics and Perfumes Supplier",
                    "Cosmetics Store",
                    "Perfume Store",
                ],
                "npages": 141,
                "nreviews": 20,
            },
            "www.granada.no.txt": {
                "name": "Granada AS",
                "rating_stats": (1, 3.7),
                "categories": [
                    "Business Administration Service",
                    "e-Commerce Service",
                    "Logistics Service",
                    "Online Marketplace",
                    "Translator",
                    "Warehouse",
                ],
                "npages": 1,
                "nreviews": 1,
            },
            "djmania.es.txt": {
                "name": "DJMania.es",
                "rating_stats": (52, 2.3),
                "categories": [
                    "e-Commerce Service",
                ],
                "npages": 3,
                "nreviews": 20,
            },
            "www.burgerking.dk.txt": {
                "name": "Burger King",
                "rating_stats": (3205, 1.9),
                "categories": [
                    "Restaurant",
                ],
                "npages": 156,
                "nreviews": 20,
            },
            "burgerking.no.txt": {
                "name": "Burger King",
                "rating_stats": (99, 2.3),
                "categories": [
                    None,
                ],
                "npages": 5,
                "nreviews": 20,
            },
            "www.burgerking.fr.txt": {
                "name": "BURGER KING FRANCE",
                "rating_stats": (775, 3.1),
                "categories": [
                    "Restaurants & Bars",
                ],
                "npages": 38,
                "nreviews": 20,
            },
            "twenix.es.txt": {
                "name": "Twenix",
                "rating_stats": (85, 4.4),
                "categories": [
                    "Educational Institution",
                ],
                "npages": 4,
                "nreviews": 20,
            },
            "elejidoshopping.es.txt": {
                "name": "elejidoshopping",
                "rating_stats": (21, 2.5),
                "categories": [
                    None,
                ],
                "npages": 2,
                "nreviews": 20,
            },
        }

        # Dummy search_data. Because the tests pages are not
        # extracted from the search's result page, we cannot
        # extract from there the score and nreviews from that
        # page, so we provide dummy data
        dummy_score = 2.5
        dummy_nreviews = 21

        self.companies = {}

        for id in self.data:
            source = os.path.join(data_dir, id)
            with open(source, encoding="utf8") as f:
                parsed_page = xray.parse_page(f, None)
                company = xray.extract_company_info(parsed_page)

                if not (company["score"] and company["nreviews"]):
                    company["score"] = dummy_score
                    company["nreviews"] = dummy_nreviews

                # Number of reviews set to 100 to extract all of them
                company["parsed_page"] = parsed_page
                company["reviews"] = get_reviews(parsed_page, True, 100, None)
                self.companies[id] = company

    def test_extract_name(self):
        """Test that the name is correctly extracted"""
        for id in self.companies:
            name = self.companies[id]["name"]
            with self.subTest(source=id):
                self.assertEqual(name, self.data[id]["name"])

    def test_extract_rating_stats(self):
        """Test that the number of reviews and score are correctly extracted"""
        for id in self.companies:
            nreviews = self.companies[id]["nreviews"]
            score = self.companies[id]["score"]
            with self.subTest(source=id):
                self.assertEqual((nreviews, score), self.data[id]["rating_stats"])

    def test_extract_categories(self):
        """
        Test that the categories extracted from a company are the correct ones
        for some example companies.
        """

        for id in self.companies:
            categories = self.companies[id]["categories"]

            if not categories:
                categories = [None]

            with self.subTest(source=id):
                self.assertEqual(categories, self.data[id]["categories"])

    def test_getnpages(self):
        """Test the extracted number of pages"""
        for id in self.companies:
            npages = xray.get_npages(self.companies[id]["parsed_page"])
            with self.subTest(source=id):
                self.assertEqual(npages, self.data[id]["npages"])

    def test_nreviews(self):
        """Test the number of reviews extracted."""
        for id in self.companies:
            n_extracted_reviews = len(self.companies[id]["reviews"])
            with self.subTest(source=id):
                self.assertEqual(n_extracted_reviews, self.data[id]["nreviews"])
