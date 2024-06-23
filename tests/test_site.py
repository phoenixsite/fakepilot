import unittest
from functools import reduce

from fakepilot import extract_reviews, search


class TestSite(unittest.TestCase):
    def test_required_attrs(self):

        query, ncompanies = "burger", 2
        required_attrs = ["phone"]

        for attr in required_attrs:
            companies = search(query, ncompanies, required_attrs=attr)
            has_attr = [attr in company for company in companies]
            check_attr = reduce(lambda x, y: x == y, has_attr, True)

            with self.subTest(attr=attr):
                self.assertEqual(check_attr, True)

    def test_number_reviews(self):
        """Tests that the number of reviews extracted is correct."""
        url = "https://es.trustpilot.com/review/www.hsnstore.com?languages=all"
        nreviews = [1, 2, 5]

        for nreview in nreviews:
            reviews = extract_reviews(url, nreview)
            with self.subTest(nreviews=nreview):
                self.assertEqual(nreview, len(reviews))
