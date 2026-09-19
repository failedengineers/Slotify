from datetime import datetime

import pytest

from slotify import (
    DSTTransitionError,
    InvalidDateRangeError,
    Slot,
    SlotGenerator,
    TimeWindow,
)


def test_basic_generation():
    generator = SlotGenerator(
        start="09:00",
        end="10:00",
        duration=30,
        timezone="Asia/Kolkata",
    )

    slots = generator.generate("2026-09-21")

    assert len(slots) == 2

    assert slots[0].start.hour == 9
    assert slots[0].start.minute == 0

    assert slots[0].duration.total_seconds() == 1800


def test_multiple_windows():
    generator = SlotGenerator(
        windows=[
            ("09:00", "12:00"),
            ("13:00", "17:00"),
        ],
        duration=60,
        timezone="Asia/Kolkata",
    )

    slots = generator.generate("2026-09-21")

    assert len(slots) == 7


def test_weekdays():
    generator = SlotGenerator(
        start="09:00",
        end="10:00",
        duration=30,
        weekdays=["monday", "wednesday"],
        timezone="Asia/Kolkata",
    )

    monday = generator.generate_for_date(
        "2026-09-21"
    )
    tuesday = generator.generate_for_date(
        "2026-09-22"
    )
    wednesday = generator.generate_for_date(
        "2026-09-23"
    )

    assert len(monday) == 2
    assert len(tuesday) == 0
    assert len(wednesday) == 2


def test_excluded_dates():
    generator = SlotGenerator(
        start="09:00",
        end="10:00",
        duration=30,
        excluded_dates=["2026-09-21"],
        timezone="Asia/Kolkata",
    )

    assert generator.generate_for_date(
        "2026-09-21"
    ) == []


def test_overnight_window():
    generator = SlotGenerator(
        start="22:00",
        end="02:00",
        duration=60,
        timezone="Asia/Kolkata",
    )

    slots = generator.generate_for_date(
        "2026-09-21"
    )

    assert len(slots) == 4

    assert slots[0].start.hour == 22
    assert slots[-1].end.hour == 2
    assert slots[-1].end.day == 22


def test_breaks():
    generator = SlotGenerator(
        start="09:00",
        end="13:00",
        duration=60,
        breaks=[
            ("10:00", "11:00"),
        ],
        timezone="Asia/Kolkata",
    )

    slots = generator.generate_for_date(
        "2026-09-21"
    )

    assert len(slots) == 3
    assert slots[0].start.hour == 9
    assert slots[1].start.hour == 11


def test_invalid_date_range():
    generator = SlotGenerator(
        start="09:00",
        end="10:00",
        duration=30,
    )

    with pytest.raises(InvalidDateRangeError):
        generator.generate(
            "2026-09-25",
            "2026-09-21",
        )


def test_dst_nonexistent_time_can_be_skipped():
    generator = SlotGenerator(
        start="01:00",
        end="03:00",
        duration=30,
        timezone="America/New_York",
        dst_nonexistent="skip",
    )

    slots = generator.generate_for_date(
        "2026-03-08"
    )

    assert len(slots) == 2


def test_dst_ambiguous_time_can_raise():
    generator = SlotGenerator(
        start="01:00",
        end="03:00",
        duration=30,
        timezone="America/New_York",
        dst_ambiguous="raise",
    )

    with pytest.raises(DSTTransitionError):
        generator.generate_for_date(
            "2026-11-01"
        )


def test_slot_duration_uses_real_elapsed_time():
    start = datetime.fromisoformat(
        "2026-11-01T01:30:00-04:00"
    )
    end = datetime.fromisoformat(
        "2026-11-01T01:30:00-05:00"
    )

    slot = Slot(start, end)

    assert slot.duration.total_seconds() == 3600


def test_upcoming_is_deterministic_with_now():
    generator = SlotGenerator(
        start="09:00",
        end="12:00",
        duration=60,
        timezone="Asia/Kolkata",
    )

    slots = generator.upcoming(
        1,
        now=datetime.fromisoformat(
            "2026-09-21T10:30:00+05:30"
        ),
    )

    assert len(slots) == 1
    assert slots[0].start.hour == 11


def test_slot_overlap():
    first = Slot(
        datetime.fromisoformat(
            "2026-09-21T09:00:00+05:30"
        ),
        datetime.fromisoformat(
            "2026-09-21T10:00:00+05:30"
        ),
    )

    second = Slot(
        datetime.fromisoformat(
            "2026-09-21T09:30:00+05:30"
        ),
        datetime.fromisoformat(
            "2026-09-21T10:30:00+05:30"
        ),
    )

    third = Slot(
        datetime.fromisoformat(
            "2026-09-21T10:00:00+05:30"
        ),
        datetime.fromisoformat(
            "2026-09-21T11:00:00+05:30"
        ),
    )

    assert first.overlaps(second)
    assert not first.overlaps(third)