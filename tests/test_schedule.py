from datetime import datetime

import pytest

from slotify import (
    ConfigurationError,
    Schedule,
    SlotGenerator,
)


def test_different_hours_per_weekday():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "17:00")],
            "wednesday": [("12:00", "20:00")],
        }
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
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

    assert len(monday) == 8
    assert len(tuesday) == 0
    assert len(wednesday) == 8

    assert monday[0].start.hour == 9
    assert wednesday[0].start.hour == 12


def test_date_override_replaces_weekly_schedule():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "12:00")],
        },
        overrides={
            "2026-09-21": [("14:00", "17:00")],
        },
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    slots = generator.generate_for_date(
        "2026-09-21"
    )

    assert len(slots) == 3
    assert slots[0].start.hour == 14
    assert slots[-1].end.hour == 17


def test_empty_override_closes_date():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "17:00")],
        },
        overrides={
            "2026-09-21": [],
        },
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    assert generator.generate_for_date(
        "2026-09-21"
    ) == []


def test_none_override_closes_date():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "17:00")],
        },
        overrides={
            "2026-09-21": None,
        },
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    assert generator.generate_for_date(
        "2026-09-21"
    ) == []


def test_override_can_open_normally_closed_day():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "17:00")],
        },
        overrides={
            "2026-09-22": [("10:00", "12:00")],
        },
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    slots = generator.generate_for_date(
        "2026-09-22"
    )

    assert len(slots) == 2


def test_numeric_weekdays_work():
    schedule = Schedule(
        weekly={
            0: [("09:00", "10:00")],
            4: [("14:00", "15:00")],
        }
    )

    assert schedule.is_open(
        "2026-09-21"
    )

    assert not schedule.is_open(
        "2026-09-22"
    )

    assert schedule.is_open(
        "2026-09-25"
    )


def test_schedule_conflicts_with_legacy_arguments():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "10:00")],
        }
    )

    with pytest.raises(ConfigurationError):
        SlotGenerator(
            schedule=schedule,
            start="09:00",
            end="17:00",
            duration=30,
            timezone="Asia/Kolkata",
        )


def test_schedule_date_range_generation():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "11:00")],
            "tuesday": [("10:00", "12:00")],
            "wednesday": [("13:00", "15:00")],
        }
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    slots = generator.generate(
        "2026-09-21",
        "2026-09-23",
    )

    assert len(slots) == 6


def test_overnight_schedule():
    schedule = Schedule(
        weekly={
            "monday": [("22:00", "02:00")],
        }
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    slots = generator.generate_for_date(
        "2026-09-21"
    )

    assert len(slots) == 4
    assert slots[0].start.hour == 22
    assert slots[-1].end.hour == 2


def test_closed_date_blocks_override():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "17:00")],
        },
        overrides={
            "2026-09-21": [("13:00", "17:00")],
        },
        closed_dates=[
            "2026-09-21",
        ],
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    assert generator.generate_for_date(
        "2026-09-21"
    ) == []

def test_annual_closed_date():
    schedule = Schedule(
        weekly={
            "friday": [("09:00", "17:00")],
        },
        annual_closed_dates=[
            "12-25",
        ],
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    assert generator.generate_for_date(
        "2026-12-25"
    ) == []

    assert generator.generate_for_date(
        "2027-12-24"
    )
def test_annual_closed_date_tuple_format():
    schedule = Schedule(
        weekly={
            "friday": [("09:00", "17:00")],
        },
        annual_closed_dates=[
            (12, 25),
        ],
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    assert generator.generate_for_date(
        "2026-12-25"
    ) == []
def test_override_can_open_normally_closed_day():
    schedule = Schedule(
        weekly={
            "monday": [("09:00", "17:00")],
        },
        overrides={
            "2026-09-27": [("10:00", "12:00")],
        },
    )

    generator = SlotGenerator(
        schedule=schedule,
        duration=60,
        timezone="Asia/Kolkata",
    )

    slots = generator.generate_for_date(
        "2026-09-27"
    )

    assert len(slots) == 2
    assert slots[0].start.hour == 10