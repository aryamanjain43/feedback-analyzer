# Feedback Analyzer

**Turn hundreds of customer reviews into a ranked list of what to fix first.**

Product teams collect feedback from app store reviews, G2, support tickets and NPS surveys, but it usually sits in a spreadsheet nobody reads. This tool groups that feedback into themes so a PM can see, in seconds, where customers are struggling and where to focus the roadmap.

## The problem

- Feedback is scattered across sources and written in free text
- Reading every review by hand does not scale past a few dozen
- Without structure, roadmap decisions lean on the loudest customer instead of the most common pain

## What it does today

- Reads a CSV of reviews (any file with a `text` column)
- Tags each review with one or more themes: Performance, Pricing, Onboarding, Integrations, Support, UI/UX
- Scores each review as positive, negative or neutral (-1 to 1) with a word list that understands simple negation like "not good" or "never solved"
- Gives each theme a 0–100 priority score and a High / Medium / Low tier
- Prints a summary sorted by priority with mention counts, share of total, % negative and an example quote per theme, plus the overall sentiment split
- Ends with a "Top 3 to fix first" list, each with a real complaint from a customer

```
Analyzed 55 reviews
Sentiment: 31% positive, 49% negative, 20% neutral

Theme          Mentions   Share  Negative  Priority  Tier    Example
----------------------------------------------------------------------------------------------------
Performance           8     15%      100%       100  High    "Pages take forever to open on mobile"
Pricing              12     22%       42%        62  Medium  "Good value for the price honestly"
UI/UX                11     20%       45%        62  Medium  "Navigation menu is confusing"
Onboarding            9     16%       44%        50  Medium  "Onboarding emails were clear and useful"
Support               8     15%       50%        50  Medium  "The help center articles are outdated"
Integrations          9     16%       22%        25  Low     "Would love a Zapier integration"

Top 3 to fix first
1. Performance (High, 100/100): 8 of 55 reviews bring it up and 8 of those are complaints.
   Customer quote: "Pages take forever to open on mobile"
2. Pricing (Medium, 62/100): 12 of 55 reviews bring it up and 5 of those are complaints.
   Customer quote: "Way too expensive for a small team"
3. UI/UX (Medium, 62/100): 11 of 55 reviews bring it up and 5 of those are complaints.
   Customer quote: "Navigation menu is confusing"
```

## How prioritization works

A theme deserves attention when lots of people mention it **and** most of them are unhappy about it. So each theme's priority is:

```
priority = (share of mentions) × (share of negative mentions)
         = (theme mentions / all reviews) × (negative mentions / theme mentions)
```

Scores are scaled 0–100 against the worst theme in the data, so the top problem always scores 100 and the rest show how close they are to it. Ties go to the theme mentioned more often.

| Tier   | Score  | What it means      |
|--------|--------|--------------------|
| High   | 70–100 | Fix now            |
| Medium | 40–69  | Plan for it        |
| Low    | 0–39   | Keep an eye on it  |

In the sample data, Performance only shows up in 15% of reviews, but every one of them is a complaint, so it outranks Pricing, which is mentioned more often but is negative in fewer than half of those reviews.

## How to run

Requires Python 3.9+. No extra packages needed.

```bash
git clone https://github.com/aryamanjain43/feedback-analyzer.git
cd feedback-analyzer
python analyze.py                       # sample data
python analyze.py path/to/your.csv      # your own reviews
```

## Roadmap

- [x] Theme tagging with an editable keyword taxonomy
- [x] Sentiment scoring (positive / negative / neutral) per review
- [x] Priority score per theme: how often it comes up × how negative it is
- [ ] Visual report with charts
- [ ] AI mode: use an LLM to discover themes the keyword list misses

## Why I built this

I'm a Master of Engineering Management student at Duke focused on product management. Prioritizing a roadmap starts with understanding customers, and this project is a small, practical version of the feedback pipeline I'd want on any product team. It pairs with my [feature-prioritizer](https://github.com/aryamanjain43/feature-prioritizer) and [market-sizer](https://github.com/aryamanjain43/market-sizer) projects.

## Project structure

```
feedback-analyzer/
├── analyze.py              # entry point
├── src/themes.py           # theme taxonomy and tagging logic
├── src/sentiment.py        # lexicon-based sentiment scoring
├── src/priority.py         # priority score and tier per theme
└── data/sample_reviews.csv # 55 sample reviews from 4 sources
```
