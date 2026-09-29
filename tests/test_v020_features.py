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
        datetime.fromisoformat("2026-09-28").date(),
        datetime.fromisoformat("2026-09-30").date(),
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


def test_resource_pool_selects_available_resource():
    store = InMemoryBookingStore()
    first = AvailabilityEngine(
        generator(),
        store=store,
        resource_id="doctor-1",
        capacity=1,
    )
    slot = generator().generate_for_date("2026-09-21")[0]
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    first.reserve(slot, now=now)

    pooled = AvailabilityEngine(
        generator(),
        store=store,
        resource_pool=("doctor-1", "doctor-2"),
        capacity=1,
    )
    result = pooled.check_availability(slot, now=now)
    assert result.available
    assert result.resource_id == "doctor-2"

    booking = pooled.reserve(slot, now=now)
    assert booking.resource_id == "doctor-2"


def test_availability_explains_policy_failure():
    policy = BookingPolicy(minimum_notice=timedelta(hours=2))
    engine = AvailabilityEngine(generator(), policy=policy)
    slot = generator().generate_for_date("2026-09-21")[0]
    result = engine.check_availability(
        slot,
        now=datetime.fromisoformat("2026-09-21T08:30:00+05:30"),
    )
    assert not result.available
    assert "minimum booking notice" in result.reason


def test_next_available_and_available_between():
    engine = AvailabilityEngine(generator())
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    first = engine.next_available("2026-09-21", now=now)
    assert first is not None
    assert first.start.hour == 9

    slots = engine.available_between(
        datetime.fromisoformat("2026-09-21T09:30:00+05:30"),
        datetime.fromisoformat("2026-09-21T12:00:00+05:30"),
        now=now,
    )
    assert len(slots) == 2
    assert slots[0].start.hour == 10


def test_available_for_duration():
    engine = AvailabilityEngine(
        SlotGenerator(
            start="09:00",
            end="13:00",
            duration=30,
            timezone="Asia/Kolkata",
        )
    )
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    slots = engine.available_for_duration(
        90,
        "2026-09-21",
        now=now,
    )
    assert slots
    assert all(slot.duration == timedelta(minutes=90) for slot in slots)


def test_booking_limits():
    policy = BookingPolicy(
        max_bookings_per_day=1,
        max_upcoming_bookings=1,
    )
    engine = AvailabilityEngine(generator(), policy=policy)
    slots = generator().generate_for_date("2026-09-21")
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    engine.reserve(slots[0], now=now)
    with pytest.raises(SlotUnavailableError):
        engine.reserve(slots[1], now=now)


def test_minimum_gap_between_bookings():
    policy = BookingPolicy(
        min_gap_between_bookings=timedelta(minutes=30),
    )
    engine = AvailabilityEngine(generator(), policy=policy)
    slots = generator().generate_for_date("2026-09-21")
    now = datetime.fromisoformat("2026-09-20T08:00:00+05:30")
    engine.reserve(slots[0], now=now)
    with pytest.raises(SlotUnavailableError):
        engine.reserve(slots[1], now=now)


def test_named_availability_schedules():
    early = generator()
    late = SlotGenerator(
        start="14:00",
        end="16:00",
        duration=60,
        timezone="Asia/Kolkata",
    )
    engine = AvailabilityEngine.from_schedules(
        {"default": early, "late": late},
        default_schedule="default",
    )
    slots = engine.available_slots(
        "2026-09-21",
        schedule_name="late",
        now=datetime.fromisoformat("2026-09-20T08:00:00+05:30"),
    )
    assert [slot.start.hour for slot in slots] == [14, 15]


def test_daily_recurrence_with_exclusion():
    rule = RecurrenceRule(
        frequency="daily",
        count=4,
        excluded_dates=("2026-09-22",),
    )
    assert list(rule.occurrences("2026-09-21")) == [
        datetime.fromisoformat("2026-09-21").date(),
        datetime.fromisoformat("2026-09-23").date(),
        datetime.fromisoformat("2026-09-24").date(),
        datetime.fromisoformat("2026-09-25").date(),
    ]


def test_monthly_recurrence():
    rule = RecurrenceRule(
        frequency="monthly",
        day_of_month=31,
        count=3,
    )
    assert list(rule.occurrences("2026-01-01")) == [
        datetime.fromisoformat("2026-01-31").date(),
        datetime.fromisoformat("2026-02-28").date(),
        datetime.fromisoformat("2026-03-31").date(),
    ]


def test_yearly_recurrence():
    rule = RecurrenceRule(
        frequency="yearly",
        day_of_month=29,
        count=3,
    )
    assert list(rule.occurrences("2024-01-01")) == [
        datetime.fromisoformat("2024-01-29").date(),
        datetime.fromisoformat("2025-01-29").date(),
        datetime.fromisoformat("2026-01-29").date(),
    ]
