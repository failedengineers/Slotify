from datetime import datetime

from slotify import AvailabilityEngine, BookingConflictError, SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

engine = AvailabilityEngine(
    generator,
    resource_id="doctor-123",
    capacity=1,
)

now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
slot = generator.generate_for_date("2026-10-05")[0]

booking = engine.reserve(slot, now=now)
print("Booked:", booking.booking_id)

try:
    engine.reserve(slot, now=now)
except BookingConflictError:
    print("Second booking rejected")

engine.cancel(booking.booking_id, now=now)
print("Cancelled")
