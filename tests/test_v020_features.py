from datetime import datetime, timedelta

import pytest

from slotify import (
    AvailabilityEngine,
    BookingConflictError,
    BookingPolicy,
    InMemoryBookingStore,
    RecurrenceRule,
    SlotGenerator,
    SlotUnavailableError,
)


def generator():
    return SlotGenerator(
        start="09:00",
        end="12:00",
        duration=60,
        timezone="Asia/Kolkata",
    )


def test_cancel_policy():
    policy = BookingPolicy(cancellation_window=timedelta(hours=2))
    engine = AvailabilityEngine(generator(), policy=policy)
    now = datetime.fromisoformat("2026-09-21T08:00:00+05:30")
    booking = engine.reserve(
        generator().generate_for_date("2026-09-21")[0],
        now=now,
    )
    with pytest.raises(SlotUnavailableError):
        engine.cancel(booking.booking_id, now=datetime.fromisoformat(
            "2026-09-21T08:00:01+05:30"
        ))


def test_reschedule():
    engine = AvailabilityEngine(generator())
    slots = generator().generate_for_date("2026-09-21")
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    booking = engine.reserve(slots[0], now=now)
    moved = engine.reschedule(booking.booking_id, slots[1], now=now)
    assert moved.booking_id == booking.booking_id
    assert moved.slot == slots[1]
    assert moved.rescheduled_count == 1


def test_reschedule_conflict_keeps_original():
    store = InMemoryBookingStore()
    engine = AvailabilityEngine(generator(), store=store)
    slots = generator().generate_for_date("2026-09-21")
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    first = engine.reserve(slots[0], now=now)
    engine.reserve(slots[1], now=now)
    with pytest.raises(BookingConflictError):
        engine.reschedule(first.booking_id, slots[1], now=now)
    assert store.get(first.booking_id).slot == slots[0]


def test_resource_ids_allow_shared_resource_constraints():
    store = InMemoryBookingStore()
    engine_a = AvailabilityEngine(
        generator(), store=store, resource_ids=("doctor-1", "room-1")
    )
    engine_b = AvailabilityEngine(
        generator(), store=store, resource_ids=("doctor-2", "room-1")
    )
    slot = generator().generate_for_date("2026-09-21")[0]
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    engine_a.reserve(slot, now=now)
    assert not engine_b.is_available(slot, now=now)


def test_recurring_rule():
    rule = RecurrenceRule(
        weekdays=(0, 2),
        count=4,
    )
    dates = list(rule.occurrences("2026-09-21"))
    assert dates == [
        datetime.fromisoformat("2026-09-21").date(),
        datetime.fromisoformat("2026-09-23").date(),
        datetime.fromisoformat("2026-10-05").date(),
        datetime.fromisoformat("2026-10-07").date(),
    ]


def test_recurring_rule_until():
    rule = RecurrenceRule(
        weekdays=(0,),
        until="2026-10-12",
    )
    assert list(rule.occurrences("2026-09-21")) == [
        datetime.fromisoformat("2026-09-21").date(),
        datetime.fromisoformat("2026-09-28").date(),
        datetime.fromisoformat("2026-10-05").date(),
        datetime.fromisoformat("2026-10-12").date(),
    ]


def test_booking_to_ics():
    engine = AvailabilityEngine(generator())
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    booking = engine.reserve(
        generator().generate_for_date("2026-09-21")[0],
        now=now,
    )
    text = booking.to_ics(summary="Doctor Appointment")
    assert "BEGIN:VCALENDAR" in text
    assert "SUMMARY:Doctor Appointment" in text
    assert "UID:" + booking.booking_id + "@slotify" in text
    assert "DTSTART:20260921T033000Z" in text


def test_reserve_recurring_creates_series():
    engine = AvailabilityEngine(generator())
    first_slot = generator().generate_for_date("2026-09-21")[0]
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")

    bookings = engine.reserve_recurring(
        first_slot,
        RecurrenceRule(weekdays=(0,), count=3),
        now=now,
    )

    assert len(bookings) == 3
    assert len({booking.series_id for booking in bookings}) == 1
    assert [booking.slot.start.date().isoformat() for booking in bookings] == [
        "2026-09-21",
        "2026-09-28",
        "2026-10-05",
    ]


def test_reserve_recurring_rolls_back_on_conflict():
    store = InMemoryBookingStore()
    engine = AvailabilityEngine(generator(), store=store)
    slots = generator().generate_for_date("2026-09-28")
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")

    engine.reserve(slots[0], now=now)

    first_slot = generator().generate_for_date("2026-09-21")[0]

    with pytest.raises(BookingConflictError):
        engine.reserve_recurring(
            first_slot,
            RecurrenceRule(weekdays=(0,), count=2),
            now=now,
        )

    remaining = store.list()
    assert len(remaining) == 1
    assert remaining[0].slot.start.date().isoformat() == "2026-09-28"
