"""HTML report: the same analysis as the terminal summary, as a page you can share.

write_report() builds one self-contained report.html. Everything is inline
(CSS and SVG charts), so the file opens offline, can be emailed or dropped
into a doc, and needs no libraries or CDNs.

The page has:
    - headline stats (reviews, sentiment split, top theme)
    - a bar chart of mentions by theme
    - a stacked bar of positive / neutral / negative per theme
    - the priority table
    - the "Top 3 to fix first" list with a customer quote each
"""

import os
from collections import Counter, defaultdict
from datetime import date
from html import escape

from src.priority import priority_scores
from src.sentiment import score_sentiment
from src.themes import tag_themes

SENTIMENTS = ("positive", "neutral", "negative")


def theme_sentiment(reviews):
    """Return theme -> Counter of positive / neutral / negative reviews."""
    mix = defaultdict(Counter)
    for r in reviews:
        label, _ = score_sentiment(r["text"])
        for theme in tag_themes(r["text"]):
            mix[theme][label] += 1
    return mix


def _pct(part, whole):
    return part / whole * 100 if whole else 0.0


def _bar(width_pct, cls, label):
    """One horizontal bar as inline SVG. It stretches to its grid cell, so it
    stays readable on a phone; the numbers sit in HTML next to it."""
    return (
        f'<svg class="bar" viewBox="0 0 100 10" preserveAspectRatio="none" role="img" aria-label="{escape(label)}">'
        f'<title>{escape(label)}</title>'
        f'<rect class="track" x="0" y="0" width="100" height="10" rx="1"/>'
        f'<rect class="{cls}" x="0" y="0" width="{width_pct:.2f}" height="10" rx="1"/>'
        f"</svg>"
    )


def _stacked(mix, theme):
    """Positive / neutral / negative segments for one theme, as inline SVG."""
    n = sum(mix.values())
    x, parts, gap = 0.0, [], 0.6
    for label in SENTIMENTS:
        w = _pct(mix[label], n)
        if w:
            tip = f"{theme}: {mix[label]} {label} ({w:.0f}%)"
            parts.append(
                f'<rect class="{label}" x="{x:.2f}" y="0" width="{max(w - gap, 0.4):.2f}" height="10">'
                f"<title>{escape(tip)}</title></rect>"
            )
            x += w
    summary = ", ".join(f"{mix[l]} {l}" for l in SENTIMENTS)
    return (
        f'<svg class="bar" viewBox="0 0 100 10" preserveAspectRatio="none" role="img" '
        f'aria-label="{escape(theme)}: {summary}">{"".join(parts)}</svg>'
    )


def build_html(reviews, source_name="reviews"):
    """Return the full report as an HTML string."""
    total = len(reviews)
    mix = theme_sentiment(reviews)
    counts = Counter({t: sum(m.values()) for t, m in mix.items()})
    negatives = Counter({t: m["negative"] for t, m in mix.items()})
    labels = Counter(score_sentiment(r["text"])[0] for r in reviews)

    examples, negative_examples = {}, {}
    for r in reviews:
        is_negative = score_sentiment(r["text"])[0] == "negative"
        for theme in tag_themes(r["text"]):
            examples.setdefault(theme, r["text"])
            if is_negative:
                negative_examples.setdefault(theme, r["text"])

    ranked = priority_scores(counts, negatives, total)
    # Same rule as the terminal report: "Other" is not a real theme, and a
    # theme nobody complains about has nothing to fix.
    top = [row for row in ranked if row[0] != "Other" and negatives[row[0]]][:3]

    # Headline stats
    top_theme = top[0][0] if top else "None"
    stats = [
        (str(total), "reviews analyzed"),
        (f"{_pct(labels['negative'], total):.0f}%", "negative overall"),
        (f"{_pct(labels['positive'], total):.0f}%", "positive overall"),
        (escape(top_theme), "fix first"),  # a word, not a number: styled smaller below
    ]
    stats_html = "".join(f'<div class="stat{" word" if i == 3 else ""}"><div class="value">{v}</div><div class="label">{l}</div></div>' for i, (v, l) in enumerate(stats))

    # Mentions by theme, most mentioned first
    by_mentions = sorted(counts, key=lambda t: (-counts[t], t))
    most = max(counts.values(), default=0)
    mention_rows = "".join(
        f'<div class="row"><span class="name">{escape(t)}</span>'
        f'{_bar(_pct(counts[t], most), "fill", f"{t}: {counts[t]} mentions")}'
        f'<span class="num">{counts[t]} <small>{_pct(counts[t], total):.0f}%</small></span></div>'
        for t in by_mentions
    )

    # Sentiment per theme, in priority order so it lines up with the table
    sentiment_rows = "".join(
        f'<div class="row"><span class="name">{escape(t)}</span>{_stacked(mix[t], t)}'
        f'<span class="num">{_pct(mix[t]["negative"], counts[t]):.0f}% <small>neg</small></span></div>'
        for t, _, _ in ranked
    )

    # Priority table
    table_rows = "".join(
        f"<tr><td>{escape(t)}</td><td class=\"r hide-sm\">{counts[t]}</td>"
        f"<td class=\"r hide-sm\">{_pct(counts[t], total):.0f}%</td>"
        f"<td class=\"r\">{_pct(negatives[t], counts[t]):.0f}%</td>"
        f"<td class=\"r\"><strong>{score}</strong></td>"
        f'<td><span class="tier {tier.lower()}">{tier}</span></td>'
        f'<td class="quote hide-sm">&ldquo;{escape(examples[t])}&rdquo;</td></tr>'
        for t, score, tier in ranked
    )

    # Top 3 to fix first
    top_items = "".join(
        f'<li><div class="top-head"><strong>{escape(t)}</strong>'
        f'<span class="tier {tier.lower()}">{tier} &middot; {score}/100</span></div>'
        f"<p>{counts[t]} of {total} reviews bring it up and {negatives[t]} of those are complaints.</p>"
        f"<blockquote>&ldquo;{escape(negative_examples[t])}&rdquo;</blockquote></li>"
        for t, score, tier in top
    )
    top_section = (
        f'<section><h2>Top {len(top)} to fix first</h2><ol class="top">{top_items}</ol></section>' if top else ""
    )

    return TEMPLATE.format(
        css=CSS,
        source=escape(source_name),
        today=date.today().strftime("%b %d, %Y").replace(" 0", " "),
        stats=stats_html,
        mention_rows=mention_rows,
        sentiment_rows=sentiment_rows,
        table_rows=table_rows,
        top_section=top_section,
    )


def write_report(reviews, path, source_name="reviews"):
    """Write the report to path (folders are created) and return the path."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_html(reviews, source_name))
    return path


CSS = """
:root {
  color-scheme: light;
  --page: #f6f6f3; --surface: #ffffff; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --line: #e4e3dc; --track: #efeee9;
  --fill: #2a78d6; --positive: #2a78d6; --neutral: #c3c2b7; --negative: #e34948;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 880px; margin: 0 auto; padding: 32px 16px 48px; }
header h1 { font-size: 26px; margin: 0 0 4px; letter-spacing: -0.01em; }
header p { margin: 0 0 24px; color: var(--ink-2); }
section { background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
  padding: 20px; margin-bottom: 16px; }
h2 { font-size: 17px; margin: 0 0 4px; }
.sub { color: var(--ink-2); margin: 0 0 16px; font-size: 14px; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
.stat .value { font-size: 28px; font-weight: 650; line-height: 1.1; overflow-wrap: anywhere; }
.stat.word .value { font-size: 22px; padding-top: 4px; }
.stat .label { color: var(--ink-2); font-size: 13px; margin-top: 4px; }
.row { display: grid; grid-template-columns: 110px 1fr 80px; align-items: center; gap: 12px; margin: 8px 0; }
.name { font-size: 14px; }
.num { font-size: 14px; text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.num small { color: var(--muted); font-size: 12px; }
svg.bar { width: 100%; height: 18px; display: block; }
svg.bar .track { fill: var(--track); }
svg.bar .fill { fill: var(--fill); }
svg.bar .positive { fill: var(--positive); }
svg.bar .neutral { fill: var(--neutral); }
svg.bar .negative { fill: var(--negative); }
.legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: var(--ink-2); margin: 0 0 8px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { padding: 10px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); font-weight: 600; }
td.r, th.r { text-align: right; font-variant-numeric: tabular-nums; }
td.quote { color: var(--ink-2); min-width: 200px; }
tr:last-child td { border-bottom: 0; }
.tier { display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 999px; white-space: nowrap; }
.tier.high { background: #fde5e4; color: #a32424; }
.tier.medium { background: #fdf0d5; color: #7a5200; }
.tier.low { background: #e8f0fb; color: #1c5cab; }
ol.top { list-style: none; counter-reset: top; margin: 12px 0 0; padding: 0; }
ol.top li { counter-increment: top; position: relative; padding: 0 0 16px 40px; }
ol.top li + li { border-top: 1px solid var(--line); padding-top: 16px; }
ol.top li::before { content: counter(top); position: absolute; left: 0; width: 28px; height: 28px;
  border-radius: 50%; background: var(--ink); color: #fff; font-weight: 600; font-size: 14px;
  display: grid; place-items: center; }
ol.top li + li::before { top: 16px; }
.top-head { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
ol.top p { margin: 4px 0 8px; color: var(--ink-2); }
blockquote { margin: 0; padding: 8px 12px; border-left: 3px solid var(--negative); background: #faf9f6; border-radius: 0 6px 6px 0; }
footer { color: var(--muted); font-size: 13px; text-align: center; margin-top: 24px; }
@media (max-width: 640px) {
  main { padding-top: 20px; }
  header h1 { font-size: 22px; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .row { grid-template-columns: 88px 1fr 72px; gap: 8px; }
  .stat.word .value { font-size: 20px; }
  .hide-sm { display: none; }  /* phone: keep the table to what fits; mentions and quotes are shown above and below */
  th, td { padding: 10px 6px; }
  section { padding: 16px; }
}
"""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Feedback Report</title>
<style>{css}</style>
</head>
<body>
<main>
<header>
  <h1>Customer Feedback Report</h1>
  <p>What customers are saying in {source}, grouped into themes and ranked by what to fix first. Generated {today}.</p>
</header>

<div class="stats">{stats}</div>

<section>
  <h2>Mentions by theme</h2>
  <p class="sub">How many reviews bring up each theme. A review can mention more than one.</p>
  {mention_rows}
</section>

<section>
  <h2>Sentiment by theme</h2>
  <p class="sub">Share of each theme's reviews that are positive, neutral or negative, in priority order.</p>
  <div class="legend"><span><i style="background:var(--positive)"></i>Positive</span><span><i style="background:var(--neutral)"></i>Neutral</span><span><i style="background:var(--negative)"></i>Negative</span></div>
  {sentiment_rows}
</section>

<section>
  <h2>Priority</h2>
  <p class="sub">Priority = share of mentions &times; share that are negative, scaled 0&ndash;100 against the worst theme.</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Theme</th><th class="r hide-sm">Mentions</th><th class="r hide-sm">Share</th><th class="r">Negative</th><th class="r">Priority</th><th>Tier</th><th class="hide-sm">Example</th></tr></thead>
    <tbody>{table_rows}</tbody>
  </table></div>
</section>

{top_section}

<footer>Made with feedback-analyzer</footer>
</main>
</body>
</html>
"""
