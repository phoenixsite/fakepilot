"""
Tests the extraction of companies' attributes.
"""

# SPDX-License-Identifier: MIT

import os
import unittest
from pathlib import Path

from fakepilot import extract_info

PARSER = "lxml"
BASE_DIR = Path(__file__).resolve().parent


class TestXray(unittest.TestCase):
    """
    Tests the extraction of the attributes in multiple pages.
    """

    # pylint: disable=consider-iterating-dictionary

    def setUp(self):
        """
        Create the real data and extract the information
        from certain local HTML pages.
        """

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

        for filename in self.data.keys():
            source = os.path.join(data_dir, filename)
            company = extract_info(source, True, 100)
            if not (company["score"] and company["nreviews"]):
                company["score"] = dummy_score
                company["nreviews"] = dummy_nreviews

            self.companies[filename] = company

    def test_extract_name(self):
        """Test that the name is correctly extracted"""
        for filename, company in self.companies.items():
            name = company["name"]
            with self.subTest(source=filename):
                self.assertEqual(name, self.data[filename]["name"])

    def test_extract_rating_stats(self):
        """Test that the number of reviews and score are correctly extracted"""
        for filename, company in self.companies.items():
            nreviews = company["nreviews"]
            score = company["score"]
            with self.subTest(source=filename):
                self.assertEqual((nreviews, score), self.data[filename]["rating_stats"])

    def test_extract_categories(self):
        """
        Test that the categories extracted from a company are the correct ones.
        """

        for filename, company in self.companies.items():
            categories = company["categories"]

            if not categories:
                categories = [None]

            with self.subTest(source=filename):
                self.assertEqual(categories, self.data[filename]["categories"])

    def test_nreviews(self):
        """Test the number of reviews extracted."""
        for filename, company in self.companies.items():
            n_extracted_reviews = len(company["reviews"])
            with self.subTest(source=filename):
                self.assertEqual(n_extracted_reviews, self.data[filename]["nreviews"])
