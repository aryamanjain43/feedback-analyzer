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
- Prints a ranked summary with mention counts, share of total, and an example quote per theme

```
Analyzed 55 reviews

Theme          Mentions   Share   Example
------------------------------------------------------------------------------
Pricing              12     22%   "Good value for the price honestly"
UI/UX                11     20%   "Navigation menu is confusing"
Integrations          9     16%   "Would love a Zapier integration"
...
```

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
- [ ] Sentiment scoring (positive / negative / neutral) per review
- [ ] Priority score per theme: how often it comes up × how negative it is
- [ ] Visual report with charts
- [ ] AI mode: use an LLM to discover themes the keyword list misses

## Why I built this

I'm a Master of Engineering Management student at Duke focused on product management. Prioritizing a roadmap starts with understanding customers, and this project is a small, practical version of the feedback pipeline I'd want on any product team. It pairs with my [feature-prioritizer](https://github.com/aryamanjain43/feature-prioritizer) and [market-sizer](https://github.com/aryamanjain43/market-sizer) projects.

## Project structure

```
feedback-analyzer/
├── analyze.py              # entry point
├── src/themes.py           # theme taxonomy and tagging logic
└── data/sample_reviews.csv # 55 sample reviews from 4 sources
```
