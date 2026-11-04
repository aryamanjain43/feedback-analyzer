"""Keyword-based theme tagging for customer feedback.

Each theme has a list of keywords. A review is tagged with every theme whose
keywords appear in its text. Reviews that match nothing land in "Other",
which is a useful signal on its own: a big "Other" bucket means the
taxonomy needs a new theme.
"""

THEMES = {
    "Performance": ["slow", "lag", "crash", "freez", "load", "forever", "speed"],
    "Pricing": ["price", "pricing", "expensive", "cheap", "bill", "fee", "plan", "value", "cost"],
    "Onboarding": ["setup", "set up", "tutorial", "getting started", "onboarding", "invite", "first time"],
    "Integrations": ["integration", "sync", "connector", "export", "slack", "zapier", "salesforce", "calendar"],
    "Support": ["support", "customer service", "agent", "help center", "reply", "chat"],
    "UI/UX": ["interface", "design", "navigat", "button", "dark mode", "cluttered", "menu"],
}


def tag_themes(text, themes=THEMES):
    """Return the list of themes whose keywords appear in the text."""
    lowered = text.lower()
    matched = [name for name, words in themes.items() if any(w in lowered for w in words)]
    return matched or ["Other"]


def review_themes(review):
    """Themes for one review row: keyword tags plus any AI mode added.

    AI mode (src/ai_themes.py) stores its picks in review["ai_themes"]. When a
    review has them, they replace "Other" and are added to keyword matches.
    """
    keyword = [t for t in tag_themes(review["text"]) if t != "Other"]
    extra = [t for t in review.get("ai_themes", []) if t not in keyword]
    return keyword + extra or ["Other"]
