"""Basic tests for theme tagging, sentiment scoring and priority ranking.

Run with: python -m unittest
"""

import unittest
from collections import Counter

from src.priority import priority_scores, tier
from src.sentiment import score_sentiment
from src.themes import review_themes, tag_themes


class ThemeTaggingTests(unittest.TestCase):
    def test_single_theme(self):
        self.assertEqual(tag_themes("Way too expensive for a small team"), ["Pricing"])

    def test_multiple_themes(self):
        themes = tag_themes("The app is slow and the pricing is confusing")
        self.assertIn("Performance", themes)
        self.assertIn("Pricing", themes)

    def test_case_insensitive(self):
        self.assertEqual(tag_themes("ZAPIER INTEGRATION please"), ["Integrations"])

    def test_no_match_is_other(self):
        self.assertEqual(tag_themes("The app does not work with my screen reader"), ["Other"])

    def test_ai_themes_replace_other(self):
        review = {"text": "Contrast is hard to read", "ai_themes": ["Accessibility"]}
        self.assertEqual(review_themes(review), ["Accessibility"])


class SentimentTests(unittest.TestCase):
    def test_positive(self):
        label, score = score_sentiment("Great product, really easy to use")
        self.assertEqual(label, "positive")
        self.assertGreater(score, 0)

    def test_negative(self):
        label, score = score_sentiment("Pages take forever to open and the app crashes")
        self.assertEqual(label, "negative")
        self.assertLess(score, 0)

    def test_negation_flips_positive(self):
        self.assertEqual(score_sentiment("Support was not helpful")[0], "negative")

    def test_feature_request_is_not_praise(self):
        self.assertNotEqual(score_sentiment("Would love a Zapier integration")[0], "positive")

    def test_neutral(self):
        self.assertEqual(score_sentiment("I use it on my laptop"), ("neutral", 0.0))

    def test_score_in_range(self):
        for text in ["good good good", "bad bad bad", "fixed my billing issue"]:
            _, score = score_sentiment(text)
            self.assertTrue(-1 <= score <= 1)


class PriorityTests(unittest.TestCase):
    def test_tiers(self):
        self.assertEqual(tier(100), "High")
        self.assertEqual(tier(70), "High")
        self.assertEqual(tier(69), "Medium")
        self.assertEqual(tier(40), "Medium")
        self.assertEqual(tier(39), "Low")

    def test_frequent_and_negative_ranks_first(self):
        counts = Counter({"Performance": 8, "Pricing": 12, "Support": 4})
        negatives = Counter({"Performance": 8, "Pricing": 5, "Support": 1})
        ranked = priority_scores(counts, negatives, total=60)
        self.assertEqual(ranked[0], ("Performance", 100, "High"))
        self.assertEqual([t for t, _, _ in ranked], ["Performance", "Pricing", "Support"])

    def test_no_complaints_scores_zero(self):
        ranked = priority_scores(Counter({"UI/UX": 5}), Counter(), total=10)
        self.assertEqual(ranked, [("UI/UX", 0, "Low")])

    def test_ties_go_to_more_mentions(self):
        # Both themes have 4 negative reviews out of 20, so equal raw priority.
        counts = Counter({"Support": 4, "Onboarding": 8})
        negatives = Counter({"Support": 4, "Onboarding": 4})
        ranked = priority_scores(counts, negatives, total=20)
        self.assertEqual([t for t, _, _ in ranked], ["Onboarding", "Support"])


if __name__ == "__main__":
    unittest.main()
