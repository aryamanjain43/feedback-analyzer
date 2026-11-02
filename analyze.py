"""Feedback Analyzer: turn a pile of customer reviews into themes.

Usage:
    python analyze.py                      # runs on the sample data
    python analyze.py path/to/reviews.csv  # your own CSV with a "text" column
"""

import csv
import sys
from collections import Counter

from src.priority import priority_scores
from src.sentiment import score_sentiment
from src.themes import tag_themes


def load_reviews(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize(reviews):
    counts = Counter()
    negatives = Counter()
    labels = Counter()
    examples = {}
    negative_examples = {}
    for r in reviews:
        label, _ = score_sentiment(r["text"])
        labels[label] += 1
        for theme in tag_themes(r["text"]):
            counts[theme] += 1
            if label == "negative":
                negatives[theme] += 1
                negative_examples.setdefault(theme, r["text"])
            examples.setdefault(theme, r["text"])
    return counts, negatives, labels, examples, negative_examples


def print_report(counts, negatives, labels, examples, negative_examples, total):
    print(f"\nAnalyzed {total} reviews")
    split = ", ".join(f"{labels[l] / total * 100:.0f}% {l}" for l in ("positive", "negative", "neutral"))
    print(f"Sentiment: {split}\n")

    ranked = priority_scores(counts, negatives, total)
    print(f"{'Theme':<14}{'Mentions':>9}{'Share':>8}{'Negative':>10}{'Priority':>10}  {'Tier':<8}Example")
    print("-" * 100)
    for theme, score, tier in ranked:
        n = counts[theme]
        share = n / total * 100
        neg = negatives[theme] / n * 100
        print(f"{theme:<14}{n:>9}{share:>7.0f}%{neg:>9.0f}%{score:>10}  {tier:<8}\"{examples[theme][:40]}\"")

    # "Other" is not a real theme, and a theme nobody complains about has nothing to fix.
    top = [row for row in ranked if row[0] != "Other" and negatives[row[0]]][:3]
    if top:
        print("\nTop 3 to fix first")
        for i, (theme, score, tier) in enumerate(top, 1):
            n, neg = counts[theme], negatives[theme]
            print(f"{i}. {theme} ({tier}, {score}/100): {n} of {total} reviews bring it up and {neg} of those are complaints.")
            print(f"   Customer quote: \"{negative_examples[theme]}\"")
    print()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_reviews.csv"
    reviews = load_reviews(path)
    counts, negatives, labels, examples, negative_examples = summarize(reviews)
    print_report(counts, negatives, labels, examples, negative_examples, len(reviews))


if __name__ == "__main__":
    main()
