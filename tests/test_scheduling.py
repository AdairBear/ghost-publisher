"""Slot arithmetic — the part most likely to quietly publish at the wrong time."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from ghost_publisher.config import Cadence
from ghost_publisher.scheduling import (
    ScheduleError,
    next_slot,
    parse_ghost_timestamp,
    to_ghost_timestamp,
)

NY = ZoneInfo("America/New_York")
WEEKLY = Cadence(
    every="weekly", weekday="tuesday", time="09:00", timezone="America/New_York"
)


def test_picks_the_coming_tuesday_from_a_sunday() -> None:
    now = datetime(2026, 8, 2, 18, 0, tzinfo=NY)  # Sunday
    slot = next_slot(WEEKLY, now=now)
    assert (slot.year, slot.month, slot.day) == (2026, 8, 4)
    assert slot.weekday() == 1
    assert (slot.hour, slot.minute) == (9, 0)


def test_a_tuesday_run_before_the_slot_uses_that_same_day() -> None:
    now = datetime(2026, 8, 4, 6, 0, tzinfo=NY)  # Tuesday 06:00, lead 60m
    slot = next_slot(WEEKLY, now=now)
    assert slot.day == 4
    assert slot.hour == 9


def test_a_tuesday_run_after_the_slot_rolls_to_next_week() -> None:
    now = datetime(2026, 8, 4, 9, 30, tzinfo=NY)
    slot = next_slot(WEEKLY, now=now)
    assert slot.day == 11


def test_min_lead_pushes_past_a_too_close_slot() -> None:
    cadence = Cadence(
        every="weekly",
        weekday="tuesday",
        time="09:00",
        timezone="America/New_York",
        min_lead_minutes=120,
    )
    now = datetime(2026, 8, 4, 8, 0, tzinfo=NY)  # 60m before the slot, lead is 120m
    slot = next_slot(cadence, now=now)
    assert slot.day == 11, "a slot inside the lead window must not be used"


def test_slot_advances_past_the_last_one_already_scheduled() -> None:
    now = datetime(2026, 8, 2, 18, 0, tzinfo=NY)
    already = datetime(2026, 8, 4, 9, 0, tzinfo=NY)
    slot = next_slot(WEEKLY, now=now, after=already)
    assert slot.day == 11, "two runs in one week must not collide on one timestamp"


def test_repeated_runs_keep_stepping_forward() -> None:
    now = datetime(2026, 8, 2, 18, 0, tzinfo=NY)
    last: datetime | None = None
    days = []
    for _ in range(4):
        last = next_slot(WEEKLY, now=now, after=last)
        days.append((last.month, last.day))
    assert days == [(8, 4), (8, 11), (8, 18), (8, 25)]


def test_biweekly_steps_fourteen_days() -> None:
    cadence = Cadence(
        every="biweekly", weekday="tuesday", time="09:00", timezone="America/New_York"
    )
    now = datetime(2026, 8, 2, 18, 0, tzinfo=NY)
    first = next_slot(cadence, now=now)
    second = next_slot(cadence, now=now, after=first)
    assert (second - first).days == 14


def test_daily_rolls_to_tomorrow_once_the_time_has_passed() -> None:
    cadence = Cadence(every="daily", time="09:00", timezone="America/New_York")
    now = datetime(2026, 8, 2, 10, 0, tzinfo=NY)
    slot = next_slot(cadence, now=now)
    assert (slot.day, slot.hour) == (3, 9)


def test_slot_survives_a_dst_transition_as_wall_clock_time() -> None:
    # US DST ends 2026-11-01. The Tuesday after is 2026-11-03.
    now = datetime(2026, 10, 28, 12, 0, tzinfo=NY)
    slot = next_slot(WEEKLY, now=now)
    assert (slot.month, slot.day, slot.hour) == (11, 3, 9)
    assert slot.utcoffset() == timedelta(hours=-5), "should be EST, not EDT"
    # 09:00 EST is 14:00 UTC; the same wall clock in EDT would have been 13:00.
    assert to_ghost_timestamp(slot) == "2026-11-03T14:00:00.000Z"


def test_ghost_timestamp_is_utc_iso8601_with_milliseconds() -> None:
    slot = datetime(2026, 8, 4, 9, 0, tzinfo=NY)
    assert to_ghost_timestamp(slot) == "2026-08-04T13:00:00.000Z"


def test_ghost_timestamp_round_trips() -> None:
    slot = datetime(2026, 8, 4, 9, 0, tzinfo=NY)
    parsed = parse_ghost_timestamp(to_ghost_timestamp(slot))
    assert parsed == slot.astimezone(timezone.utc)


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ScheduleError):
        to_ghost_timestamp(datetime(2026, 8, 4, 9, 0))
    with pytest.raises(ScheduleError):
        next_slot(WEEKLY, now=datetime(2026, 8, 4, 9, 0))


def test_unknown_timezone_is_rejected() -> None:
    with pytest.raises(ScheduleError):
        next_slot(Cadence(timezone="Mars/Olympus_Mons"))


def test_local_timezone_produces_an_aware_future_slot() -> None:
    slot = next_slot(Cadence())  # timezone: local, real clock
    assert slot.tzinfo is not None
    assert slot > datetime.now().astimezone()
