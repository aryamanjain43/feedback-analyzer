"""AI mode: ask an LLM to find the themes the keyword list misses.

The keyword tagger is fast and predictable, but it only knows the themes we
wrote down. Reviews that match nothing land in "Other". This module sends
those reviews to Claude through the Anthropic API, asks it to propose a few
new themes and to assign each review to one, and hands the result back so
the normal report can include the new themes.

It is optional. The rest of the tool never imports the SDK, and this module
only imports it inside discover_themes(), so the default path still runs
with zero installs. Setup:

    pip install -r requirements-ai.txt
    export ANTHROPIC_API_KEY=...   # never commit a key
    python analyze.py --ai

Set ANTHROPIC_MODEL to use a different model than the default.
"""

import os

from src.themes import THEMES, tag_themes

DEFAULT_MODEL = "claude-sonnet-4-5"
BATCH_SIZE = 40      # reviews per API call; keeps each prompt small
MAX_NEW_THEMES = 5   # per batch, so the model groups instead of labeling every review

SYSTEM_PROMPT = (
    "You are a product manager's research assistant. You group customer reviews "
    "into themes a product team can act on. Theme names are short (one to three "
    "words, Title Case) and describe the product area, not the sentiment: "
    "'Accessibility', not 'Accessibility complaints'."
)

TOOL = {
    "name": "record_themes",
    "description": "Record the themes found in the reviews and which review belongs to which theme.",
    "input_schema": {
        "type": "object",
        "properties": {
            "themes": {
                "type": "array",
                "description": "New themes found in these reviews.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Short theme name in Title Case."},
                        "description": {"type": "string", "description": "One sentence on what the theme covers."},
                    },
                    "required": ["name", "description"],
                },
            },
            "assignments": {
                "type": "array",
                "description": "One entry per review that fits a theme. Leave out reviews that fit none.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "The review id from the list."},
                        "theme": {"type": "string", "description": "A theme name from 'themes' or the known themes."},
                    },
                    "required": ["id", "theme"],
                },
            },
        },
        "required": ["themes", "assignments"],
    },
}


class AIModeUnavailable(Exception):
    """Raised with a friendly, printable message when AI mode cannot run."""


def _client():
    """Return an Anthropic client, or raise AIModeUnavailable explaining why not."""
    try:
        import anthropic  # imported here so the default path needs no install
    except ImportError:
        raise AIModeUnavailable(
            "AI mode needs the Anthropic Python SDK. Install it with:\n"
            "    pip install -r requirements-ai.txt"
        )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise AIModeUnavailable(
            "AI mode needs an Anthropic API key. Create one at https://console.anthropic.com/ and set it with:\n"
            "    export ANTHROPIC_API_KEY=your-key-here"
        )
    return anthropic, anthropic.Anthropic()


def _prompt(batch, known_themes):
    lines = "\n".join(f"{i}. {text}" for i, text in batch)
    return (
        f"Known themes (already covered by our keyword tagger, or found in earlier batches): "
        f"{', '.join(known_themes)}.\n\n"
        f"These customer reviews did not match any keyword theme. Propose up to {MAX_NEW_THEMES} new themes "
        f"that cover them, then assign each review to one theme. Reuse a known theme name when a review "
        f"clearly fits it. Only create a theme if at least two reviews share it, or one review raises a "
        f"clearly distinct product area. Leave out reviews that are too vague to place.\n\n"
        f"Reviews:\n{lines}"
    )


def _ask(client, model, batch, known_themes):
    """One API call. Returns the tool input dict: {"themes": [...], "assignments": [...]}."""
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": TOOL["name"]},
        messages=[{"role": "user", "content": _prompt(batch, known_themes)}],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL["name"]:
            return block.input
    return {"themes": [], "assignments": []}


def discover_themes(reviews, all_reviews=False, model=None):
    """Find new themes with Claude and attach them to the reviews.

    By default only reviews the keyword tagger left in "Other" are sent.
    With all_reviews=True every review is sent, so the model can also add
    a second theme to reviews that already matched a keyword.

    Each review the model places gets an "ai_themes" list, which
    src.themes.review_themes() uses in place of (or on top of) the keyword
    tags. Returns {theme name: description} for the new themes that ended
    up with at least one review. Raises AIModeUnavailable with a friendly
    message if the SDK, the key or the API call fails.
    """
    anthropic, client = _client()
    model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

    targets = [
        (i, r["text"]) for i, r in enumerate(reviews)
        if all_reviews or tag_themes(r["text"]) == ["Other"]
    ]
    if not targets:
        return {}

    known = list(THEMES)  # grows as batches find new themes, so names stay consistent
    descriptions = {}
    assigned = {}  # review index -> list of AI themes
    for start in range(0, len(targets), BATCH_SIZE):
        batch = targets[start:start + BATCH_SIZE]
        try:
            result = _ask(client, model, batch, known)
        except anthropic.AuthenticationError:
            raise AIModeUnavailable("The Anthropic API rejected the key in ANTHROPIC_API_KEY. Check it and try again.")
        except anthropic.APIError as e:
            raise AIModeUnavailable(f"The Anthropic API call failed: {e}")

        for theme in result.get("themes", []):
            name = str(theme.get("name", "")).strip()
            if name and name not in known:
                known.append(name)
                descriptions[name] = str(theme.get("description", "")).strip()

        batch_ids = {i for i, _ in batch}
        for item in result.get("assignments", []):
            idx, name = item.get("id"), str(item.get("theme", "")).strip()
            # Ignore anything we did not ask about or a theme the model never named.
            if idx in batch_ids and name in known and name != "Other":
                assigned.setdefault(idx, [])
                if name not in assigned[idx]:
                    assigned[idx].append(name)

    used = set()
    for idx, names in assigned.items():
        reviews[idx]["ai_themes"] = names
        used.update(names)
    return {name: desc for name, desc in descriptions.items() if name in used}
