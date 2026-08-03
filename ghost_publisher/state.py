"""Local record of what has already been sent to Ghost.

This file is the primary defence against double-publishing. It is written
*before* the source file is moved, so a crash between the API call and the
move still leaves an accurate record.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .scheduling import parse_ghost_timestamp

logger = logging.getLogger(__name__)

STATE_VERSION = 1


class StateError(Exception):
    """Raised when the state file exists but cannot be used."""


@dataclass(frozen=True)
class PublishRecord:
    """One post that has been created on Ghost."""

    source_file: str
    content_hash: str
    title: str
    post_id: str
    post_url: str
    slug: str
    scheduled_at: str
    created_at: str
    dry_run: bool = False


class State:
    """The `state/published.json` document."""

    def __init__(self, path: Path, records: list[PublishRecord]) -> None:
        self.path = path
        self.records = records

    @classmethod
    def load(cls, path: Path) -> State:
        """Read the state file, tolerating a missing one.

        Args:
            path: Path to `published.json`.

        Returns:
            The loaded state, empty when the file does not exist yet.

        Raises:
            StateError: The file exists but is corrupt. Failing loud here is
                deliberate — a silently-reset state file means republishing.
        """
        if not path.exists():
            return cls(path, [])
        try:
            raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StateError(
                f"state file {path} is unreadable/corrupt ({exc}). Refusing to run: "
                "a reset state file would republish already-published pieces. "
                "Fix or delete it deliberately."
            ) from exc

        records = [PublishRecord(**entry) for entry in raw.get("published", [])]
        return cls(path, records)

    def save(self) -> None:
        """Write the state file atomically (temp file + rename)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": STATE_VERSION,
            "published": [asdict(record) for record in self.records],
        }
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)
        logger.debug("state written: %s (%d records)", self.path, len(self.records))

    def add(self, record: PublishRecord) -> None:
        """Append a record and persist immediately."""
        self.records.append(record)
        self.save()

    def live_records(self) -> list[PublishRecord]:
        """Records for real posts only — dry-run entries are never stored."""
        return [record for record in self.records if not record.dry_run]

    def find_duplicate(
        self, *, source_file: str, content_hash: str
    ) -> PublishRecord | None:
        """Find an existing record matching this piece.

        Matches on either the source filename or the content hash, so both
        "same file run twice" and "same piece renamed" are caught.

        Args:
            source_file: Queue filename.
            content_hash: `QueueItem.content_hash`.

        Returns:
            The matching record, or None.
        """
        for record in self.live_records():
            if record.source_file == source_file or record.content_hash == content_hash:
                return record
        return None

    def last_scheduled_at(self) -> datetime | None:
        """The latest slot already handed to Ghost, as an aware UTC datetime.

        Returns:
            The maximum `scheduled_at` across live records, or None.
        """
        moments: list[datetime] = []
        for record in self.live_records():
            try:
                moments.append(parse_ghost_timestamp(record.scheduled_at))
            except Exception:  # noqa: BLE001 - one bad row must not blind us
                logger.warning(
                    "state record for %s has an unparseable scheduled_at %r",
                    record.source_file,
                    record.scheduled_at,
                )
        return max(moments) if moments else None
