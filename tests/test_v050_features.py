from datetime import datetime, timedelta

import pytest

from slotify import (
    AvailabilityEngine,
    BookingPolicy,
    BusyPeriod,
    BookingConflictError,
    SlotGenerator,
)


def make_generator():
    return SlotGenerator(
        start="09:00",
        end="12:00",
        duration=60,
        timezone="Asia/Kolkata",
    )


def test_external_busy_period_blocks_availability():
    policy = BookingPolicy(
        busy_periods=(
            BusyPeriod(
                start=datetime.fromisoformat("2026-10-05T10:00:00+05:30"),
                end=datetime.fromisoformat("2026-10-05T11:00:00+05:30"),
                reason="Google Calendar event",
            ),
        )
    )
    engine = AvailabilityEngine(make_generator(), policy=policy)
    slots = engine.available_slots(
        "2026-10-05",
        now=datetime.fromisoformat("2026-10-04T08:00:00+05:30"),
    )
    assert [slot.start.hour for slot in slots] == [9, 11]


def test_availability_result_exposes_machine_readable_code():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    hold = engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T09:00:00+05:30"),
        now=datetime.fromisoformat("2026-10-04T08:00:00+05:30"),
    )
    result = engine.check_availability(
        slot,
        now=datetime.fromisoformat("2026-10-04T08:30:00+05:30"),
    )
    assert result.available is False
    assert result.code == "hold_conflict"
    engine.release_hold(hold.hold_id)


def test_direct_reserve_cannot_bypass_non_pool_hold():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T09:00:00+05:30"),
        now=now,
    )
    with pytest.raises(BookingConflictError):
        engine.reserve(slot, now=now)


def test_idempotency_key_returns_same_booking():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    first = engine.reserve(
        slot,
        idempotency_key="checkout-123",
        now=datetime.fromisoformat("2026-10-04T08:00:00+05:30"),
    )
    second = engine.reserve(
        slot,
        idempotency_key="checkout-123",
        now=datetime.fromisoformat("2026-10-04T08:00:00+05:30"),
    )
    assert second.booking_id == first.booking_id
    assert len(engine.store.list()) == 1


def test_different_idempotency_keys_still_conflict():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    engine.reserve(slot, idempotency_key="one", now=now)
    with pytest.raises(BookingConflictError):
        engine.reserve(slot, idempotency_key="two", now=now)
