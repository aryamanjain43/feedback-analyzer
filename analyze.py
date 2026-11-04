"""Feedback Analyzer: turn a pile of customer reviews into themes.

Usage:
    python analyze.py                      # runs on the sample data
    python analyze.py path/to/reviews.csv  # your own CSV with a "text" column
    python analyze.py --html               # also writes output/report.html
    python analyze.py --ai                 # optional: Claude finds themes the keywords miss
"""

import argparse
import csv
import os
import sys
from collections import Counter

from src.priority import priority_scores
from src.report import write_report
from src.sentiment import score_sentiment
from src.ai_themes import AIModeUnavailable, discover_themes
from src.themes import review_themes


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
        for theme in review_themes(r):
            counts[theme] += 1
            if label == "negative":
                negatives[theme] += 1
                negative_examples.setdefault(theme, r["text"])
            examples.setdefault(theme, r["text"])
    return counts, negatives, labels, examples, negative_examples


def print_report(counts, negatives, labels, examples, negative_examples, total, ai_themes=None):
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
        name = theme + ("*" if ai_themes and theme in ai_themes else "")
        print(f"{name:<14}{n:>9}{share:>7.0f}%{neg:>9.0f}%{score:>10}  {tier:<8}\"{examples[theme][:40]}\"")

    # "Other" is not a real theme, and a theme nobody complains about has nothing to fix.
    top = [row for row in ranked if row[0] != "Other" and negatives[row[0]]][:3]
    if top:
        print("\nTop 3 to fix first")
        for i, (theme, score, tier) in enumerate(top, 1):
            n, neg = counts[theme], negatives[theme]
            print(f"{i}. {theme} ({tier}, {score}/100): {n} of {total} reviews bring it up and {neg} of those are complaints.")
            print(f"   Customer quote: \"{negative_examples[theme]}\"")
    if ai_themes:
        print("\n* Found by AI mode")
        for theme, description in ai_themes.items():
            print(f"  {theme} ({counts[theme]}): {description}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Group customer reviews into themes and rank what to fix first.")
    parser.add_argument("path", nargs="?", default="data/sample_reviews.csv", help="CSV with a 'text' column")
    parser.add_argument("--html", nargs="?", const="output/report.html", metavar="FILE",
                        help="also write a visual HTML report (default: output/report.html)")
    parser.add_argument("--ai", action="store_true",
                        help="use Claude to find themes in reviews the keywords tag as 'Other' "
                             "(needs: pip install -r requirements-ai.txt and ANTHROPIC_API_KEY)")
    parser.add_argument("--ai-all", action="store_true",
                        help="with --ai, send every review instead of only 'Other' ones")
    args = parser.parse_args()

    reviews = load_reviews(args.path)
    ai_themes = {}
    if args.ai or args.ai_all:
        try:
            print("AI mode: asking Claude to find themes the keyword list missed...")
            ai_themes = discover_themes(reviews, all_reviews=args.ai_all)
            if not ai_themes:
                print("AI mode: no new themes found.")
        except AIModeUnavailable as e:
            print(f"\nAI mode is not available: {e}\nContinuing with keyword themes only.", file=sys.stderr)

    counts, negatives, labels, examples, negative_examples = summarize(reviews)
    print_report(counts, negatives, labels, examples, negative_examples, len(reviews), ai_themes)
    if args.html:
        out = write_report(reviews, args.html, source_name=os.path.basename(args.path), ai_themes=ai_themes)
        print(f"HTML report written to {out}\n")


if __name__ == "__main__":
    main()
