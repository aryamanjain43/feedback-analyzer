"""Priority scoring: which themes should the team fix first?

A theme matters more when it comes up often AND when people are unhappy
about it. So each theme gets:

    raw = (share of mentions) x (share of negative mentions)
        = (theme mentions / total reviews) x (negative mentions / theme mentions)

The raw values are then scaled 0-100 against the worst theme in the data
set, so the top theme always scores 100 and the rest read as "how close to
the top problem is this?". Ties are broken by mention count.

Tiers make the list easy to scan:
    High   70-100  fix now
    Medium 40-69   plan for it
    Low     0-39   keep an eye on it
"""

HIGH_CUTOFF = 70
MEDIUM_CUTOFF = 40


def tier(score):
    """Return High / Medium / Low for a 0-100 priority score."""
    if score >= HIGH_CUTOFF:
        return "High"
    if score >= MEDIUM_CUTOFF:
        return "Medium"
    return "Low"


def priority_scores(counts, negatives, total):
    """Return a list of (theme, score, tier) sorted from most to least urgent.

    counts:    theme -> number of reviews mentioning it
    negatives: theme -> number of negative reviews mentioning it
    total:     number of reviews analyzed
    """
    raw = {}
    for theme, n in counts.items():
        share = n / total if total else 0.0
        negative_share = negatives.get(theme, 0) / n if n else 0.0
        raw[theme] = share * negative_share

    top = max(raw.values(), default=0.0)
    scored = []
    for theme, value in raw.items():
        score = round(value / top * 100) if top else 0
        scored.append((theme, score, tier(score)))
    scored.sort(key=lambda row: (-row[1], -counts[row[0]], row[0]))
    return scored
