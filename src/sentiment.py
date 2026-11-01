"""Lexicon-based sentiment scoring for customer feedback.

Each review is split into words and matched against small positive and
negative word lists. A negator ("not", "never", "no", ...) flips the next
sentiment word within a few words, so "not good" counts as negative and
"never solved" counts as negative too. A negator that has nothing to flip
("No tutorial", "could not figure out") usually means something is missing
or failed, so it counts as a mild negative on its own.

Feature requests ("would love", "would be nice", "please add") are stripped
before scoring: wanting a feature is not the same as liking the product.

The score runs from -1 (all negative) to 1 (all positive).
"""

import re

# word -> weight. Words that settle a complaint ("fixed", "solved") weigh more
# so "fixed my billing issue" reads as positive.
POSITIVE = {
    "good": 1, "great": 1, "love": 1, "loved": 1, "clean": 1, "helpful": 1,
    "friendly": 1, "fast": 1, "quick": 1, "clear": 1, "useful": 1, "easy": 1,
    "value": 1, "works": 1, "nice": 1, "intuitive": 1, "simple": 1,
    "excellent": 1, "awesome": 1, "smooth": 1, "reliable": 1,
    "fixed": 2, "solved": 2, "resolved": 2,
}

NEGATIVE = {
    "bad": 1, "badly": 1, "slow": 1, "lag": 1, "lags": 1, "crash": 1,
    "crashes": 1, "freezing": 1, "freezes": 1, "forever": 1, "expensive": 1,
    "confusing": 1, "cluttered": 1, "hard": 1, "outdated": 1, "annoying": 1,
    "hidden": 1, "broken": 1, "breaking": 1, "doubled": 1, "too": 1,
    "issue": 1, "problem": 1, "bug": 1, "buggy": 1, "terrible": 1,
    "awful": 1, "worst": 1, "frustrating": 1, "useless": 1, "took": 1,
}

NEGATORS = {"not", "never", "no", "dont", "doesnt", "didnt", "isnt", "wasnt", "cant", "cannot", "wont"}
NEGATION_WINDOW = 3  # how many words ahead a negator reaches

REQUEST_PHRASES = ["would love", "would be nice", "would like", "please add", "i wish", "need an", "need a"]

THRESHOLD = 0.2  # scores inside (-0.2, 0.2) are neutral


def score_sentiment(text):
    """Return (label, score) where label is positive / negative / neutral."""
    lowered = text.lower()
    for phrase in REQUEST_PHRASES:
        lowered = lowered.replace(phrase, " ")
    words = re.findall(r"[a-z]+", lowered.replace("'", ""))

    total, weight_sum = 0.0, 0.0
    pending_negation = 0  # words left in the current negation window
    for word in words:
        if word in NEGATORS:
            if pending_negation:  # previous negator never found a target
                total, weight_sum = total - 0.5, weight_sum + 0.5
            pending_negation = NEGATION_WINDOW
            continue
        value = POSITIVE.get(word, 0) - NEGATIVE.get(word, 0)
        if value:
            if pending_negation:
                value = -value
                pending_negation = 0
            total += value
            weight_sum += abs(value)
        elif pending_negation:
            pending_negation -= 1
            if not pending_negation:  # window ran out with nothing to flip
                total, weight_sum = total - 0.5, weight_sum + 0.5
    if pending_negation:
        total, weight_sum = total - 0.5, weight_sum + 0.5

    score = total / weight_sum if weight_sum else 0.0
    if score >= THRESHOLD:
        label = "positive"
    elif score <= -THRESHOLD:
        label = "negative"
    else:
        label = "neutral"
    return label, round(score, 2)
