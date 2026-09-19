from datetime import datetime

import pytest

from slotify import (
    AvailabilityEngine,
    BookingConflictError,
    InMemoryBookingStore,
    SlotGenerator,
)
from concurrent.futures import ThreadPoolExecutor

def make_generator():
    return SlotGenerator(
        start="09:00",
        end="11:00",
        duration=60,
        timezone="Asia/Kolkata",
    )


def test_first_slot_is_available():
    engine = AvailabilityEngine(
        make_generator()
    )

    slots = engine.available_slots(
        "2026-09-21"
    )

    assert len(slots) == 2


def test_booking_removes_slot_from_availability():
    engine = AvailabilityEngine(
        make_generator()
    )

    slots = engine.available_slots(
        "2026-09-21"
    )

    booking = engine.reserve(
        slots[0]
    )

    assert booking.status == "confirmed"

    remaining = engine.available_slots(
        "2026-09-21"
    )

    assert len(remaining) == 1
    assert remaining[0].start.hour == 10


def test_double_booking_is_rejected():
    store = InMemoryBookingStore(
        capacity=1
    )

    engine = AvailabilityEngine(
        make_generator(),
        store=store,
    )

    slot = engine.generator.generate_for_date(
        "2026-09-21"
    )[0]

    engine.reserve(slot)

    with pytest.raises(BookingConflictError):
        engine.reserve(slot)


def test_capacity_allows_multiple_bookings():
    store = InMemoryBookingStore(
        capacity=2
    )

    engine = AvailabilityEngine(
        make_generator(),
        store=store,
        capacity=2,
    )

    slot = engine.generator.generate_for_date(
        "2026-09-21"
    )[0]

    first = engine.reserve(slot)
    second = engine.reserve(slot)

    assert first.booking_id != second.booking_id

    with pytest.raises(BookingConflictError):
        engine.reserve(slot)


def test_buffer_blocks_adjacent_booking():
    generator = SlotGenerator(
        start="09:00",
        end="12:00",
        duration=60,
        timezone="Asia/Kolkata",
    )

    engine = AvailabilityEngine(
        generator,
        buffer_after=15,
    )

    first = generator.generate_for_date(
        "2026-09-21"
    )[0]

    second = generator.generate_for_date(
        "2026-09-21"
    )[1]

    engine.reserve(first)

    assert not engine.is_available(second)


def test_cancel_makes_slot_available():
    engine = AvailabilityEngine(
        make_generator()
    )

    slot = engine.generator.generate_for_date(
        "2026-09-21"
    )[0]

    booking = engine.reserve(slot)

    assert not engine.is_available(slot)

    engine.cancel(booking.booking_id)

    assert engine.is_available(slot)


def test_resource_capacity_is_independent():
    store = InMemoryBookingStore(
        capacity=1
    )

    doctor_a = AvailabilityEngine(
        make_generator(),
        store=store,
        resource_id="doctor-a",
    )

    doctor_b = AvailabilityEngine(
        make_generator(),
        store=store,
        resource_id="doctor-b",
    )

    slot = make_generator().generate_for_date(
        "2026-09-21"
    )[0]

    doctor_a.reserve(slot)

    assert not doctor_a.is_available(slot)
    assert doctor_b.is_available(slot)


def test_reserve_first_available():
    engine = AvailabilityEngine(
        make_generator()
    )

    booking = engine.reserve_first_available(
        "2026-09-21"
    )

    assert booking.slot.start.hour == 9


def test_booking_protection_interval():
    engine = AvailabilityEngine(
        make_generator(),
        buffer_before=10,
        buffer_after=15,
    )

    slot = make_generator().generate_for_date(
        "2026-09-21"
    )[0]

    booking = engine.reserve(slot)

    assert (
        booking.protected_start.hour == 8
    )

    assert (
        booking.protected_start.minute == 50
    )

    assert (
        booking.protected_end.hour == 10
    )

    assert (
        booking.protected_end.minute == 15
    )

    from datetime import datetime, timedelta, timezone
from datetime import datetime, timedelta, timezone

from slotify import (
    BlockedPeriod,
    BookingPolicy,
    SlotUnavailableError,
)
def test_minimum_notice():
    generator = SlotGenerator(
        start="09:00",
        end="12:00",
        duration=60,
        timezone="Asia/Kolkata",
    )

    policy = BookingPolicy(
        minimum_notice=timedelta(hours=2),
    )

    engine = AvailabilityEngine(
        generator,
        policy=policy,
    )

    now = datetime.fromisoformat(
        "2026-09-21T08:00:00+05:30"
    )

    available = engine.available_slots(
        "2026-09-21",
        now=now,
    )

    assert len(available) == 2
    assert available[0].start.hour == 10
def test_blocked_period():
    generator = SlotGenerator(
        start="09:00",
        end="13:00",
        duration=60,
        timezone="Asia/Kolkata",
    )

    blocked = BlockedPeriod(
        start=datetime.fromisoformat(
            "2026-09-21T10:00:00+05:30"
        ),
        end=datetime.fromisoformat(
            "2026-09-21T12:00:00+05:30"
        ),
        reason="Provider unavailable",
    )

    policy = BookingPolicy(
        blocked_periods=(blocked,),
    )

    engine = AvailabilityEngine(
        generator,
        policy=policy,
    )

    now = datetime.fromisoformat(
        "2026-09-20T10:00:00+05:30"
    )

    slots = engine.available_slots(
        "2026-09-21",
        now=now,
    )

    assert len(slots) == 2
    assert slots[0].start.hour == 9
    assert slots[1].start.hour == 12
    
def test_reserve_rechecks_policy():
    generator = SlotGenerator(
        start="09:00",
        end="10:00",
        duration=60,
        timezone="Asia/Kolkata",
    )

    policy = BookingPolicy(
        minimum_notice=timedelta(hours=2),
    )

    engine = AvailabilityEngine(
        generator,
        policy=policy,
    )

    slot = generator.generate_for_date(
        "2026-09-21"
    )[0]

    now = datetime.fromisoformat(
        "2026-09-21T08:30:00+05:30"
    )

    with pytest.raises(SlotUnavailableError):
        engine.reserve(
            slot,
            now=now,
        )

def test_concurrent_booking_allows_only_one_when_capacity_is_one():
    store = InMemoryBookingStore(capacity=1)

    engine = AvailabilityEngine(
        make_generator(),
        store=store,
        capacity=1,
    )

    slot = engine.generator.generate_for_date(
        "2026-09-21"
    )[0]

    def attempt():
        try:
            return engine.reserve(slot)
        except BookingConflictError:
            return None

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(
            executor.map(
                lambda _: attempt(),
                range(20),
            )
        )

    successful = [
        result
        for result in results
        if result is not None
    ]

    assert len(successful) == 1

    bookings = store.list()

    assert len(bookings) == 1