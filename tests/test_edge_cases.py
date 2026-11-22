"""
Tests the behaviour of the extraction functions when the expected
tags are missing or incomplete.
"""

# SPDX-License-Identifier: MIT

import unittest
import zipfile
from pathlib import Path

from fakepilot import extract_info, xray

BASE_DIR = Path(__file__).resolve().parent
EMPTY_PAGE = "<html><body><div></div></body></html>"


def parse(html):
    """Parse a HTML snippet."""
    return xray.parse_page(html)


class TestMissingTags(unittest.TestCase):
    """
    Tests that the functions raise an error, or return an empty value,
    when the page doesn't have the tags they look for.
    """

    def test_missing_country(self):
        """The review's country is required."""
        with self.assertRaises(RuntimeError):
            xray.extract_authors_country_v1(parse(EMPTY_PAGE))

    def test_missing_date_experience_v1(self):
        """The date of experience is required on old pages."""
        with self.assertRaises(RuntimeError):
            xray.extract_date_experience_v1(parse(EMPTY_PAGE))

    def test_missing_date_experience_v2(self):
        """The date of experience is required on current pages."""
        with self.assertRaises(RuntimeError):
            xray.extract_date_experience_v2(parse(EMPTY_PAGE))

    def test_missing_rating_stats_v2(self):
        """The reviews heading is required on current pages."""
        with self.assertRaises(RuntimeError):
            xray.extract_rating_stats_v2(parse(EMPTY_PAGE))

    def test_rating_stats_v2_without_number(self):
        """The reviews heading must contain the number of reviews."""
        page = parse('<h2 class="styles_allReviewsHeading__a1">All reviews</h2>')
        with self.assertRaises(RuntimeError):
            xray.extract_rating_stats_v2(page)

    def test_missing_url(self):
        """Without the page's URL there is no company's URL."""
        self.assertIsNone(xray.extract_url(parse(EMPTY_PAGE)))

    def test_url_from_canonical_link(self):
        """The URL is also taken from the canonical link."""
        page = parse(
            '<head><link rel="canonical" '
            'href="https://es.trustpilot.com/review/company.es?page=2"></head>'
        )
        self.assertEqual(xray.extract_url(page), "company.es")

    def test_no_rating_distribution(self):
        """Without the side bar there is no rating distribution."""
        self.assertIsNone(xray.extract_percentage_stars(parse(EMPTY_PAGE)))

    def test_partial_rating_distribution(self):
        """Ratings without a row in the side bar are ``None``."""
        page = parse(
            '<div class="styles_businessInfoSideBar__a1">'
            '<label data-star-rating="five">'
            '<div class="rating-distribution-row_barValue__a1" style="width:80%">'
            "</div></label></div>"
        )
        self.assertEqual(
            xray.extract_percentage_stars(page),
            {1: None, 2: None, 3: None, 4: None, 5: 80.0},
        )

    def test_category_without_link(self):
        """Categories can be plain text instead of links."""
        page = parse(
            '<ul><li data-business-unit-info-category-typography="true">'
            " Hotel </li></ul>"
        )
        self.assertEqual(xray.extract_categories(page), ["Hotel"])


class TestExtractInfo(unittest.TestCase):
    """Tests the options of ``extract_info``."""

    def test_without_reviews(self):
        """Reviews are only extracted when they are requested."""
        with zipfile.ZipFile(BASE_DIR / "data" / "text_files.zip") as files:
            page = files.read("text_files/www.burgerking.dk_2026.txt").decode("utf-8")

        company = extract_info(page)
        self.assertEqual(company["name"], "Burger King")
        self.assertNotIn("reviews", company)
