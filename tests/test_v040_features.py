from datetime import datetime, timedelta

import pytest

from slotify import (
    AvailabilityEngine,
    BookingConflictError,
    HoldExpiredError,
    BookingHold,
    InMemoryHoldStore,
    SlotGenerator,
)


def make_generator():
    return SlotGenerator(
        start="09:00",
        end="12:00",
        duration=60,
        timezone="Asia/Kolkata",
    )


def test_hold_blocks_slot_until_released():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    hold = engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T08:15:00+05:30"),
        now=now,
    )
    assert isinstance(hold, BookingHold)
    assert not engine.is_available(slot, now=now)
    engine.release_hold(hold.hold_id)
    assert engine.is_available(slot, now=now)


def test_expired_hold_does_not_block_slot():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T09:00:00+05:30")
    engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T08:30:00+05:30"),
        now=datetime.fromisoformat("2026-10-04T08:00:00+05:30"),
    )
    assert engine.is_available(slot, now=now)


def test_confirm_hold_creates_booking_and_releases_hold():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    hold = engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T09:00:00+05:30"),
        now=now,
    )
    booking = engine.confirm_hold(hold.hold_id, now=now)
    assert booking.slot == slot
    assert engine.is_available(slot, now=now) is False


def test_hold_cannot_be_confirmed_after_expiry():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    created = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    hold = engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T08:15:00+05:30"),
        now=created,
    )
    with pytest.raises(HoldExpiredError):
        engine.confirm_hold(
            hold.hold_id,
            now=datetime.fromisoformat("2026-10-04T08:16:00+05:30"),
        )


def test_round_robin_resource_strategy():
    store_engine = AvailabilityEngine(
        make_generator(),
        resource_pool=("a", "b"),
        resource_strategy="round_robin",
    )
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    first = store_engine.reserve(slot, now=now)
    assert first.resource_id == "a"

    second = store_engine.reserve(
        make_generator().generate_for_date("2026-10-05")[1],
        now=now,
    )
    assert second.resource_id == "b"


def test_least_loaded_resource_strategy():
    store_engine = AvailabilityEngine(
        make_generator(),
        resource_id="a",
    )
    slots = make_generator().generate_for_date("2026-10-05")
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    store_engine.reserve(slots[0], now=now)

    engine = AvailabilityEngine(
        make_generator(),
        resource_pool=("a", "b"),
        resource_strategy="least_loaded",
        store=store_engine.store,
    )
    booking = engine.reserve(slots[0], now=now)
    assert booking.resource_id == "b"


def test_invalid_resource_strategy():
    with pytest.raises(ValueError):
        AvailabilityEngine(
            make_generator(),
            resource_pool=("a", "b"),
            resource_strategy="random",
        )


def test_round_robin_availability_checks_do_not_advance_selection():
    engine = AvailabilityEngine(
        make_generator(),
        resource_pool=("a", "b"),
        resource_strategy="round_robin",
    )
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")

    first = engine.check_availability(slot, now=now)
    second = engine.check_availability(slot, now=now)

    assert first.resource_id == "a"
    assert second.resource_id == "a"

    booking = engine.reserve(slot, now=now)
    assert booking.resource_id == "a"

    third = engine.check_availability(slot, now=now)
    assert third.resource_id == "b"
