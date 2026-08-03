"""Markdown to the format Ghost stores.

Ghost's canonical post format is Lexical, but the Admin API will do that
conversion for us when a post is created with `?source=html`. So this module
only has to produce clean HTML — no Lexical or Mobiledoc handling anywhere in
this project, which is what keeps it small.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# `extra` gives tables, fenced code, footnotes and definition lists.
# `sane_lists` stops stray list renumbering. `smarty` gives real quotes/dashes.
MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "smarty"]


class RenderError(Exception):
    """Raised when Markdown cannot be converted to HTML."""


def markdown_to_html(body: str) -> str:
    """Render Markdown to the HTML Ghost ingests.

    Args:
        body: Markdown source, frontmatter already stripped.

    Returns:
        Rendered HTML.

    Raises:
        RenderError: The `Markdown` package is missing, or rendering failed.
    """
    try:
        import markdown  # imported lazily so --help works without the dep
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RenderError(
            "the `Markdown` package is not installed — run "
            "`pip install -r requirements.txt`"
        ) from exc

    try:
        html = markdown.markdown(body, extensions=MARKDOWN_EXTENSIONS)
    except Exception as exc:  # markdown raises assorted types on bad input
        raise RenderError(f"markdown rendering failed: {exc}") from exc

    if not html.strip():
        raise RenderError("markdown rendered to empty HTML — refusing to publish")
    return html
