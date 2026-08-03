"""Working out the next publish slot.

The slot is a wall-clock local time (e.g. Tuesday 09:00) converted to UTC for
Ghost. Slots are computed against *both* the current time and the last slot
already handed to Ghost, so two runs in the same week cannot collide on one
timestamp.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import Cadence

logger = logging.getLogger(__name__)

# Guard against a pathological config sending the loop to the moon.
MAX_SLOT_ADVANCES = 520  # ~10 years of weekly slots


class ScheduleError(Exception):
    """Raised when a slot cannot be computed."""


def resolve_timezone(name: str) -> ZoneInfo | None:
    """Resolve a cadence timezone name.

    Args:
        name: An IANA timezone name, or "local" for the system timezone.

    Returns:
        A `ZoneInfo`, or None meaning "use the system local timezone".

    Raises:
        ScheduleError: The name is not a known timezone.
    """
    if not name or name.lower() == "local":
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ScheduleError(f"unknown timezone {name!r}: {exc}") from exc


def now_in(tz: ZoneInfo | None) -> datetime:
    """Current time as an aware datetime in the given (or system) timezone."""
    if tz is None:
        return datetime.now().astimezone()
    return datetime.now(tz)


def _at_time(day: datetime, hour: int, minute: int) -> datetime:
    """Same calendar day as `day`, at the given wall-clock time."""
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def next_slot(
    cadence: Cadence,
    *,
    now: datetime | None = None,
    after: datetime | None = None,
) -> datetime:
    """Compute the next publish slot as an aware local datetime.

    The returned slot is strictly later than `now + min_lead_minutes` and
    strictly later than `after` (the last slot already scheduled on Ghost).

    Args:
        cadence: The configured cadence.
        now: Override for the current time; defaults to real now in the
            cadence timezone. Must be timezone-aware if given.
        after: The most recent slot already handed to Ghost, if any.

    Returns:
        The next slot, timezone-aware, in the cadence timezone.

    Raises:
        ScheduleError: The timezone is unknown, or no slot could be found.
    """
    tz = resolve_timezone(cadence.timezone)
    current = now or now_in(tz)
    if current.tzinfo is None:
        raise ScheduleError("`now` must be timezone-aware")
    if tz is not None:
        current = current.astimezone(tz)

    earliest = current + timedelta(minutes=cadence.min_lead_minutes)
    hour, minute = cadence.hour_minute

    if cadence.every == "daily":
        candidate = _at_time(earliest, hour, minute)
        if candidate <= earliest:
            candidate = _at_time(earliest + timedelta(days=1), hour, minute)
    else:
        days_ahead = (cadence.weekday_index - earliest.weekday()) % 7
        candidate = _at_time(earliest + timedelta(days=days_ahead), hour, minute)
        if candidate <= earliest:
            candidate = _at_time(
                earliest + timedelta(days=days_ahead + 7), hour, minute
            )

    step = timedelta(days=cadence.interval_days)
    advances = 0
    while after is not None and candidate <= after.astimezone(candidate.tzinfo):
        candidate = _at_time(candidate + step, hour, minute)
        advances += 1
        if advances > MAX_SLOT_ADVANCES:
            raise ScheduleError(
                "could not find a slot after the last scheduled post — "
                f"gave up after {MAX_SLOT_ADVANCES} advances"
            )

    return candidate


def to_ghost_timestamp(moment: datetime) -> str:
    """Format an aware datetime the way the Ghost Admin API expects it.

    Args:
        moment: A timezone-aware datetime.

    Returns:
        An ISO-8601 UTC timestamp with milliseconds, e.g.
        `2026-08-04T16:00:00.000Z`.

    Raises:
        ScheduleError: The datetime is naive.
    """
    if moment.tzinfo is None:
        raise ScheduleError("refusing to format a naive datetime for Ghost")
    utc = moment.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond // 1000:03d}Z"


def parse_ghost_timestamp(value: str) -> datetime:
    """Parse a timestamp previously written by `to_ghost_timestamp`.

    Args:
        value: An ISO-8601 timestamp, `Z` suffix tolerated.

    Returns:
        An aware datetime in UTC.

    Raises:
        ScheduleError: The value is not parseable.
    """
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ScheduleError(f"unparseable timestamp {value!r}: {exc}") from exc
