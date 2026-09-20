# Getting Started

## Install

~~~bash
pip install slotify-scheduling
~~~

## Your first generator

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate("2026-09-21", "2026-09-21")

for slot in slots:
    print(slot.start, slot.end)
~~~

## Add a weekly schedule

~~~python
from slotify import Schedule, SlotGenerator

schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "tuesday": [("09:00", "17:00")],
        "wednesday": [("12:00", "20:00")],
        "thursday": [("09:00", "17:00")],
        "friday": [("09:00", "14:00")],
    }
)

generator = SlotGenerator(
    schedule=schedule,
    duration=30,
    timezone="Asia/Kolkata",
)
~~~

## Add booking

~~~python
from slotify import AvailabilityEngine

engine = AvailabilityEngine(
    generator,
    resource_id="provider-123",
    capacity=1,
)

available = engine.available_slots("2026-09-21")

if available:
    booking = engine.reserve(available[0])
~~~

## Understand the layers

- Schedule: when does this resource normally work?
- SlotGenerator: what slots does that schedule produce?
- AvailabilityEngine: which slots can be booked?
- BookingPolicy: which booking times are restricted?
- Booking: what reservation was created?

## Typical application flow

1. Store provider/resource configuration in your app.
2. Build the Schedule.
3. Build the SlotGenerator.
4. Generate or query slots.
5. Apply availability and booking rules.
6. Show times to the user.
7. Reserve the selected slot.
8. Persist application-level booking information.
