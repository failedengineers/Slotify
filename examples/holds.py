from datetime import datetime

from slotify import AvailabilityEngine, HoldExpiredError, SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="12:00",
    duration=60,
    timezone="Asia/Kolkata",
)

engine = AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2"),
)

slot = generator.generate_for_date("2026-10-05")[0]
created = datetime.fromisoformat("2026-10-04T08:00:00+05:30")

hold = engine.hold(
    slot,
    expires_at=datetime.fromisoformat("2026-10-04T08:15:00+05:30"),
    now=created,
)

assert not engine.is_available(slot, now=created)

booking = engine.confirm_hold(hold.hold_id, now=created)
assert booking.resource_id in {"doctor-1", "doctor-2"}

try:
    engine.confirm_hold(
        hold.hold_id,
        now=datetime.fromisoformat("2026-10-04T08:20:00+05:30"),
    )
except Exception:
    pass

print("Confirmed:", booking.booking_id)
