import unittest
from functools import reduce

from fakepilot import search, get_company


class TestSite(unittest.TestCase):
    def test_required_attrs(self):

        query, ncompanies = "burger", 12
        companies = search(query, ncompanies, with_reviews=True, nreviews=2)
        self.assertEqual(len(companies), ncompanies)

    def test_number_reviews(self):
        """Tests that the number of reviews extracted is correct."""
        url = "https://es.trustpilot.com/review/www.hsnstore.com?languages=all"
        nreviews = [22]

        for nreview in nreviews:
            company = get_company(url, with_reviews=True, nreviews=nreview)
            with self.subTest(nreviews=nreview):
                self.assertEqual(nreview, len(company["reviews"]))
