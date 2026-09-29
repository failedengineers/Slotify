# Core Concepts

Slotify is easiest to understand when you separate four things: **schedule**, **slots**, **availability**, and **bookings**.

## The flow

~~~text
Schedule rules
     |
     v
SlotGenerator
     |
     v
Generated slots
     |
     v
AvailabilityEngine
     |
     +--> booking policy
     +--> capacity
     +--> resources
     +--> existing bookings
     |
     v
Bookable slots
     |
     v
Booking
~~~

A generated slot is only a time interval. It becomes bookable after the availability and booking rules are applied.

## Schedule

Schedule describes recurring working hours and exceptions.

~~~python
from slotify import Schedule

schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "tuesday": [("09:00", "17:00")],
        "wednesday": [("09:00", "17:00")],
        "thursday": [("09:00", "17:00")],
        "friday": [("09:00", "14:00")],
    }
)
~~~

A weekday can have multiple windows:

~~~python
schedule = Schedule(
    weekly={
        "monday": [
            ("09:00", "13:00"),
            ("14:00", "18:00"),
        ],
    }
)
~~~

Use an empty list for a closed weekday.

## SlotGenerator

SlotGenerator turns scheduling rules into timezone-aware Slot objects.

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate_for_date("2026-10-05")
~~~

Generate a date range:

~~~python
slots = generator.generate(
    "2026-10-05",
    "2026-10-09",
)
~~~

Generate only future slots:

~~~python
slots = generator.upcoming(7)
~~~

Pass now explicitly when you need deterministic behavior in tests.

## Slot

A Slot represents one appointment interval.

Useful properties and methods include:

~~~text
start
end
duration
start_utc
end_utc
overlaps()
contains()
in_timezone()
to_dict()
~~~

Example:

~~~python
slot = slots[0]

print(slot.start)
print(slot.end)
print(slot.duration)

print(slot.to_dict())
~~~

Convert the same instant to another timezone:

~~~python
new_york_slot = slot.in_timezone("America/New_York")
~~~

## AvailabilityEngine

AvailabilityEngine adds bookability and reservation behavior to generated slots.

~~~python
from slotify import AvailabilityEngine

engine = AvailabilityEngine(
    generator,
    resource_id="doctor-123",
    capacity=1,
)

available = engine.available_slots("2026-10-05")
~~~

Reserve a slot:

~~~python
booking = engine.reserve(available[0])
print(booking.booking_id)
~~~

## Booking

A Booking is the reservation returned by reserve().

It includes:

~~~text
booking_id
status
slot
resource_id
resource_ids
series_id
rescheduled_count
buffer_before
buffer_after
created_at
metadata
~~~

A booking is immutable. Operations such as cancel and reschedule return a new Booking value representing the updated state.

## BookingPolicy

BookingPolicy applies business restrictions to generated slots.

~~~python
from datetime import timedelta
from slotify import BookingPolicy

policy = BookingPolicy(
    minimum_notice=timedelta(hours=2),
    maximum_horizon=timedelta(days=30),
    cancellation_window=timedelta(hours=12),
    reschedule_window=timedelta(hours=6),
    max_reschedules=2,
)
~~~

It can also contain explicit BlockedPeriod values.

## BookingStore

BookingStore is the storage interface used by the booking layer.

Slotify includes InMemoryBookingStore.

It is useful for:

~~~text
unit tests
local development
simple single-process services
~~~

For multi-worker or distributed applications, use a durable database-backed implementation and make reserve/reschedule atomic in the database.

## Resources and capacity

A resource is whatever is being booked.

Examples:

~~~text
doctor-123
room-4
barber-chair-2
laser-machine-1
yoga-class-evening
~~~

One resource:

~~~python
AvailabilityEngine(
    generator,
    resource_id="doctor-123",
)
~~~

Multiple resources:

~~~python
AvailabilityEngine(
    generator,
    resource_ids=("doctor-123", "room-4"),
)
~~~

Group capacity:

~~~python
AvailabilityEngine(
    generator,
    resource_id="yoga-evening",
    capacity=10,
)
~~~

## Buffers

Buffers expand the protected interval used for conflicts.

~~~python
engine = AvailabilityEngine(
    generator,
    resource_id="chair-2",
    buffer_before=10,
    buffer_after=15,
)
~~~

A 10:00-10:30 appointment protects 09:50-10:45 for overlap checks.

## What Slotify does not own

Slotify is a scheduling engine, not a complete booking SaaS.

Your application should normally own:

- users and authentication
- providers and business data
- permissions
- payments
- notifications
- durable database models
- frontend and API routing

Slotify stays focused on scheduling rules, availability, and booking conflicts.
