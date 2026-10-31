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
