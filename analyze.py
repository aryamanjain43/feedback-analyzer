"""Feedback Analyzer: turn a pile of customer reviews into themes.

Usage:
    python analyze.py                      # runs on the sample data
    python analyze.py path/to/reviews.csv  # your own CSV with a "text" column
"""

import csv
import sys
from collections import Counter

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
    for r in reviews:
        label, _ = score_sentiment(r["text"])
        labels[label] += 1
        for theme in tag_themes(r["text"]):
            counts[theme] += 1
            if label == "negative":
                negatives[theme] += 1
            examples.setdefault(theme, r["text"])
    return counts, negatives, labels, examples


def print_report(counts, negatives, labels, examples, total):
    print(f"\nAnalyzed {total} reviews")
    split = ", ".join(f"{labels[l] / total * 100:.0f}% {l}" for l in ("positive", "negative", "neutral"))
    print(f"Sentiment: {split}\n")
    print(f"{'Theme':<14}{'Mentions':>9}{'Share':>8}{'Negative':>10}   Example")
    print("-" * 88)
    for theme, n in counts.most_common():
        share = n / total * 100
        neg = negatives[theme] / n * 100
        print(f"{theme:<14}{n:>9}{share:>7.0f}%{neg:>9.0f}%   \"{examples[theme][:40]}\"")
    print()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_reviews.csv"
    reviews = load_reviews(path)
    counts, negatives, labels, examples = summarize(reviews)
    print_report(counts, negatives, labels, examples, len(reviews))


if __name__ == "__main__":
    main()
