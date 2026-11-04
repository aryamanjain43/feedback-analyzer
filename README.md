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
- With `--html`, also writes a one-page visual report with charts you can open in any browser or send to your team
- With `--ai` (optional), asks Claude to find new themes in the reviews the keyword list tags as "Other"

```
Analyzed 63 reviews
Sentiment: 27% positive, 52% negative, 21% neutral

Theme          Mentions   Share  Negative  Priority  Tier    Example
----------------------------------------------------------------------------------------------------
Performance           8     13%      100%       100  High    "Pages take forever to open on mobile"
Other                 8     13%       75%        75  High    "The app does not work with my screen rea"
Pricing              12     19%       42%        62  Medium  "Good value for the price honestly"
UI/UX                11     17%       45%        62  Medium  "Navigation menu is confusing"
Onboarding            9     14%       44%        50  Medium  "Onboarding emails were clear and useful"
Support               8     13%       50%        50  Medium  "The help center articles are outdated"
Integrations          9     14%       22%        25  Low     "Would love a Zapier integration"

Top 3 to fix first
1. Performance (High, 100/100): 8 of 63 reviews bring it up and 8 of those are complaints.
   Customer quote: "Pages take forever to open on mobile"
2. Pricing (Medium, 62/100): 12 of 63 reviews bring it up and 5 of those are complaints.
   Customer quote: "Way too expensive for a small team"
3. UI/UX (Medium, 62/100): 11 of 63 reviews bring it up and 5 of those are complaints.
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
python analyze.py --html                # also writes output/report.html
python analyze.py your.csv --html my_report.html   # pick the file name
python analyze.py --ai                  # optional AI mode, see below
```

## Visual report

`--html` writes a single self-contained HTML file (inline CSS and SVG charts, no internet or extra packages needed) with:

- Headline stats: reviews analyzed, % negative, % positive and the theme to fix first
- A bar chart of mentions by theme
- A stacked bar of positive / neutral / negative reviews per theme
- The priority table with tiers
- The "Top 3 to fix first" list with a customer quote for each

It works on desktop and phone, so it is easy to share in Slack or email. See an example generated from the sample data: [docs/sample_report.html](docs/sample_report.html). Reports go to `output/`, which is ignored by git.

## AI mode

The keyword list only knows the themes someone wrote down. Anything else lands in "Other", and in the sample data that bucket ranks second: 8 reviews about screen readers, contrast and personal data that no keyword catches. AI mode sends those reviews to Claude through the Anthropic API, asks it to propose new themes and assign each review to one, and merges the result into the normal terminal and HTML report. New themes are marked `*` in the terminal and `AI` in the HTML report, with a one-line description of each.

It is optional. Without `--ai` the tool still needs no installs.

1. Install the SDK: `pip install -r requirements-ai.txt`
2. Get an API key from the [Anthropic Console](https://console.anthropic.com/) and set it in your shell (never commit it):
   ```bash
   export ANTHROPIC_API_KEY=your-key-here
   ```
3. Run it:
   ```bash
   python analyze.py --ai --html           # only "Other" reviews go to the API
   python analyze.py --ai-all              # send every review, in batches, to catch extra themes
   ```

Set `ANTHROPIC_MODEL` to use a different Claude model. If the SDK or key is missing, the tool says so and falls back to keyword themes. Useful AI themes are worth copying into `src/themes.py` so the free keyword path catches them next time.

## Roadmap

- [x] Theme tagging with an editable keyword taxonomy
- [x] Sentiment scoring (positive / negative / neutral) per review
- [x] Priority score per theme: how often it comes up × how negative it is
- [x] Visual report with charts
- [x] AI mode: use an LLM to discover themes the keyword list misses

## Why I built this

I'm a Master of Engineering Management student at Duke focused on product management. Prioritizing a roadmap starts with understanding customers, and this project is a small, practical version of the feedback pipeline I'd want on any product team. It pairs with my [feature-prioritizer](https://github.com/aryamanjain43/feature-prioritizer) and [market-sizer](https://github.com/aryamanjain43/market-sizer) projects.

## Project structure

```
feedback-analyzer/
├── analyze.py              # entry point
├── src/themes.py           # theme taxonomy and tagging logic
├── src/sentiment.py        # lexicon-based sentiment scoring
├── src/priority.py         # priority score and tier per theme
├── src/report.py           # self-contained HTML report with charts
├── src/ai_themes.py        # optional AI mode: Claude finds new themes
├── requirements-ai.txt     # only needed for AI mode
├── docs/sample_report.html # example report from the sample data
└── data/sample_reviews.csv # 63 sample reviews from 4 sources
```
