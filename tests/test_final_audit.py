from datetime import datetime

import pytest

from slotify import AvailabilityEngine, BookingConflictError, SlotGenerator


def make_generator():
    return SlotGenerator(
        start="09:00",
        end="12:00",
        duration=60,
        timezone="Asia/Kolkata",
    )


def test_hold_tracks_all_required_resources():
    engine = AvailabilityEngine(
        make_generator(),
        resource_ids=("room", "therapist"),
    )
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    hold = engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T09:00:00+05:30"),
        now=now,
    )
    assert hold.resource_ids == ("room", "therapist")
    assert engine.check_availability(slot, now=now).available is False
    with pytest.raises(BookingConflictError):
        engine.reserve(slot, now=now)


def test_multi_resource_hold_confirm_preserves_resource_requirements():
    engine = AvailabilityEngine(
        make_generator(),
        resource_ids=("room", "therapist"),
    )
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    hold = engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T09:00:00+05:30"),
        now=now,
    )
    booking = engine.confirm_hold(hold.hold_id, now=now)
    assert booking.resource_ids == ("room", "therapist")
    assert booking.resource_id == "room"


def test_unscoped_hold_still_works():
    engine = AvailabilityEngine(make_generator())
    slot = make_generator().generate_for_date("2026-10-05")[0]
    now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
    hold = engine.hold(
        slot,
        expires_at=datetime.fromisoformat("2026-10-04T09:00:00+05:30"),
        now=now,
    )
    assert hold.resource_ids == ()
    with pytest.raises(BookingConflictError):
        engine.reserve(slot, now=now)
