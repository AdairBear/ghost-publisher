"""Reading the queue of Markdown pieces.

The queue is just a folder of `.md` files. Files are processed in filename
order, which is why the convention is a numeric prefix (`01-`, `02-`, ...).
Each file carries a small YAML frontmatter block.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# A piece that still contains this marker is an unfilled placeholder and is
# never published, no matter what `ready:` says.
PLACEHOLDER_MARKER = "PLACEHOLDER-DO-NOT-PUBLISH"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


class QueueError(Exception):
    """Raised when a queue file cannot be parsed or is invalid."""


@dataclass(frozen=True)
class QueueItem:
    """One Markdown piece waiting to be published."""

    path: Path
    title: str
    body: str
    tags: list[str]
    featured: bool
    ready: bool
    slug: str | None
    excerpt: str | None
    web_only: bool
    skip_reason: str | None

    @property
    def publishable(self) -> bool:
        """True when nothing blocks this item from being scheduled."""
        return self.skip_reason is None

    @property
    def content_hash(self) -> str:
        """Stable digest of title + body, used for idempotency bookkeeping."""
        digest = hashlib.sha256()
        digest.update(self.title.encode("utf-8"))
        digest.update(b"\0")
        digest.update(self.body.encode("utf-8"))
        return digest.hexdigest()


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split a Markdown document into its frontmatter mapping and body.

    Args:
        text: Full file contents.

    Returns:
        Tuple of (frontmatter dict, body markdown). The dict is empty when the
        file has no frontmatter block.

    Raises:
        QueueError: The frontmatter block is present but is not valid YAML,
            or does not parse to a mapping.
    """
    match = FRONTMATTER_RE.match(text.lstrip("﻿"))
    if not match:
        return {}, text

    raw_front, body = match.group(1), match.group(2)
    try:
        data = yaml.safe_load(raw_front)
    except yaml.YAMLError as exc:
        raise QueueError(f"frontmatter is not valid YAML: {exc}") from exc

    if data is None:
        return {}, body
    if not isinstance(data, dict):
        raise QueueError("frontmatter must be a mapping of key: value")
    return data, body


def _coerce_tags(value: Any) -> list[str]:
    """Normalize the `tags` frontmatter value into a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple)):
        return [str(part).strip() for part in value if str(part).strip()]
    raise QueueError(f"tags must be a list or comma-separated string, got {value!r}")


def load_item(path: Path) -> QueueItem:
    """Parse a single queue file.

    A file that is unfinished (placeholder marker, `ready: false`, empty body,
    or missing title) is returned with `skip_reason` set rather than raising —
    the caller logs it and moves to the next item.

    Args:
        path: Path to the `.md` file.

    Returns:
        The parsed `QueueItem`.

    Raises:
        QueueError: The file is unreadable or its frontmatter is malformed.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise QueueError(f"cannot read {path.name}: {exc}") from exc

    front, body = split_frontmatter(text)
    body = body.strip()

    title = str(front.get("title") or "").strip()
    tags = _coerce_tags(front.get("tags"))
    featured = bool(front.get("feature", front.get("featured", False)))
    # Absent `ready` means ready — a hand-dropped file with just a title works.
    ready = bool(front.get("ready", True))
    slug = str(front["slug"]).strip() if front.get("slug") else None
    excerpt = str(front["excerpt"]).strip() if front.get("excerpt") else None
    web_only = bool(front.get("web_only", False))

    skip_reason: str | None = None
    if PLACEHOLDER_MARKER in text:
        skip_reason = "still a placeholder (contains PLACEHOLDER-DO-NOT-PUBLISH)"
    elif not ready:
        skip_reason = "frontmatter says ready: false"
    elif not title:
        skip_reason = "frontmatter has no title"
    elif not body:
        skip_reason = "body is empty"

    return QueueItem(
        path=path,
        title=title,
        body=body,
        tags=tags,
        featured=featured,
        ready=ready,
        slug=slug,
        excerpt=excerpt,
        web_only=web_only,
        skip_reason=skip_reason,
    )


def list_queue(queue_dir: Path) -> list[QueueItem]:
    """Load every `.md` file in the queue directory, in filename order.

    Files whose frontmatter is malformed are logged and skipped rather than
    aborting the whole run — one bad file must not block the rest of the queue.

    Args:
        queue_dir: The queue folder.

    Returns:
        Queue items sorted by filename (so `01-` comes before `02-`).
    """
    if not queue_dir.is_dir():
        logger.warning("queue directory does not exist: %s", queue_dir)
        return []

    items: list[QueueItem] = []
    for path in sorted(queue_dir.glob("*.md"), key=lambda p: p.name.lower()):
        if path.name.upper() == "README.MD":
            continue
        try:
            items.append(load_item(path))
        except QueueError as exc:
            logger.error("skipping unparseable queue file %s: %s", path.name, exc)
    return items


def next_publishable(items: list[QueueItem]) -> QueueItem | None:
    """Return the first item that is actually ready to go.

    Args:
        items: Queue items in order.

    Returns:
        The top publishable item, or None when the queue holds nothing ready.
    """
    for item in items:
        if item.publishable:
            return item
        logger.info("skipping %s — %s", item.path.name, item.skip_reason)
    return None
