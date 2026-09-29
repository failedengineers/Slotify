from datetime import datetime

from slotify import AvailabilityEngine, SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="13:00",
    duration=60,
    timezone="Asia/Kolkata",
)

now = datetime.fromisoformat("2026-10-04T08:00:00+05:30")
slots = generator.generate_for_date("2026-10-05")

engine = AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2", "doctor-3"),
    resource_strategy="least_loaded",
)

first = engine.reserve(slots[0], now=now)
second = engine.reserve(slots[0], now=now)

assert {first.resource_id, second.resource_id} == {"doctor-1", "doctor-2"}

print(first.resource_id, second.resource_id)
