"""
Tests the extraction of companies' attributes.
"""

# SPDX-License-Identifier: MIT

import json
import os
from datetime import datetime
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
        Create the real data and extract the information from certain local
        HTML pages.
        """

        data_dir = os.path.join(BASE_DIR, "data")

        with open(os.path.join(data_dir, "valid_data.json"), encoding="utf-8") as f:
            self.data = json.load(f)

        for _filename, company_data in self.data.items():
            if "reviews" in company_data:
                for review in company_data["reviews"]:
                    review["date"] = datetime.fromisoformat(review["date"])

        # Dummy search_data. Because the tests pages are not
        # extracted from the search's result page, we cannot
        # extract from there the score and nreviews from that
        # page, so we provide dummy data
        dummy_score = 2.5
        dummy_nreviews = 21

        self.companies = {}

        for filename in self.data.keys():
            source = os.path.join(data_dir, filename)
            with self.subTest(source=filename):
                company = extract_info(source, with_reviews=True, nreviews=100)
                if not (company["score"] and company["nreviews"]):
                    company["score"] = dummy_score
                    company["nreviews"] = dummy_nreviews

                self.companies[filename] = company

    def test_extract_name(self):
        """Test that the name is correctly extracted"""
        for filename, company in self.companies.items():
            with self.subTest(source=filename):
                self.assertEqual(company["name"], self.data[filename]["name"])

    def test_extract_rating_stats(self):
        """Test that the number of reviews and score are correctly extracted"""
        for filename, company in self.companies.items():
            with self.subTest(source=filename):
                self.assertEqual(
                    [company["nreviews"], company["score"]],
                    self.data[filename]["rating_stats"],
                )

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
            with self.subTest(source=filename):
                self.assertEqual(
                    len(company["reviews"]), self.data[filename]["nreviews"]
                )

    def test_address(self):
        """Test that the address is correctly extracted."""
        for filename, company in self.companies.items():
            with self.subTest(source=filename):
                self.assertEqual(company["address"], self.data[filename]["address"])

    def test_phone(self):
        """Test that the phone number is correctly extracted."""
        for filename, company in self.companies.items():
            with self.subTest(source=filename):
                self.assertEqual(company["phone"], self.data[filename]["phone"])

    def test_email(self):
        """Test that the email address is correctly extracted."""
        for filename, company in self.companies.items():
            with self.subTest(source=filename):
                self.assertEqual(company["email"], self.data[filename]["email"])

    def test_reviews(self):
        """Test that some reviews are correctly extracted."""
        for filename, company in self.companies.items():
            if "reviews" in self.data[filename]:
                with self.subTest(source=filename):
                    # We probably have less reviews in the valid data
                    # than extracted
                    for review in self.data[filename]["reviews"]:
                        self.assertIn(review, company["reviews"])
