# Getting Started

This page gets you from **zero to a working appointment backend**.

The fastest path is:

1. install Slotify
2. define working hours
3. generate slots
4. add an availability engine
5. reserve a slot
6. add the rules your application actually needs

You do **not** need Django, a database, or a frontend to learn the core API.

## 1. Install

~~~bash
pip install slotify-scheduling
~~~

Check the installed version:

~~~bash
python -c "import slotify; print(slotify.__version__)"
~~~

## 2. Your first working scheduler

Start with one provider who works from 9:00 to 17:00 and accepts 30-minute appointments.

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate("2026-10-05")

for slot in slots[:3]:
    print(slot.start, "->", slot.end)
~~~

The important idea is:

**SlotGenerator creates possible slots. It does not know whether somebody has already booked them.**

## 3. Make the slots bookable

Use AvailabilityEngine when your application needs bookings, capacity, resources, policies, or conflicts.

~~~python
from slotify import AvailabilityEngine

engine = AvailabilityEngine(
    generator,
    resource_id="provider-123",
    capacity=1,
)

available = engine.available_slots("2026-10-05")

booking = engine.reserve(available[0])

print(booking.booking_id)
~~~

Trying to reserve the same slot again raises BookingConflictError.

~~~python
from slotify import BookingConflictError

try:
    engine.reserve(available[0])
except BookingConflictError:
    print("Someone already booked this slot.")
~~~

## 4. Build a realistic weekly schedule

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

## 5. Add breaks

~~~python
generator = SlotGenerator(
    start="09:00",
    end="18:00",
    duration=30,
    breaks=[("13:00", "14:00")],
    timezone="Asia/Kolkata",
)
~~~

## 6. Add holidays and one-off changes

~~~python
schedule = Schedule(
    weekly={"monday": [("09:00", "17:00")]},
    overrides={
        "2026-10-12": [("13:00", "18:00")],
        "2026-10-19": [],
    },
    closed_dates=["2026-10-02"],
)
~~~

An empty override closes that date.

## 7. Add booking rules

~~~python
from datetime import timedelta
from slotify import BookingPolicy

policy = BookingPolicy(
    minimum_notice=timedelta(hours=2),
    maximum_horizon=timedelta(days=30),
    cancellation_window=timedelta(hours=12),
)

engine = AvailabilityEngine(
    generator,
    resource_id="provider-123",
    policy=policy,
)
~~~

## 8. Add a resource pool

If a customer can be served by **any one** of several providers, use a pool.

~~~python
engine = AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2", "doctor-3"),
    resource_strategy="least_loaded",
)

booking = engine.reserve(
    generator.generate_for_date("2026-10-05")[0]
)

print(booking.resource_id)
~~~

Available strategies:

- first_available — use the configured order
- round_robin — rotate through resources
- least_loaded — prefer the resource with the fewest overlapping bookings

## 9. Hold a slot during checkout

Temporary holds are useful when a customer selects a slot and needs time to complete payment.

~~~python
from datetime import datetime

hold = engine.hold(
    slot,
    expires_at=datetime.fromisoformat("2026-10-05T09:10:00+05:30"),
    now=datetime.fromisoformat("2026-10-05T09:00:00+05:30"),
)

booking = engine.confirm_hold(
    hold.hold_id,
    now=datetime.fromisoformat("2026-10-05T09:05:00+05:30"),
)
~~~

Release it when checkout is abandoned:

~~~python
engine.release_hold(hold.hold_id)
~~~

An expired hold stops blocking availability automatically in the included in-memory hold store.

For distributed production systems, implement HoldStore using the same database/concurrency guarantees as your booking store.

## 10. Recurring appointments

~~~python
from slotify import RecurrenceRule

template = generator.generate_for_date("2026-10-05")[0]

series = engine.reserve_recurring(
    template,
    RecurrenceRule(
        weekdays=(0,),
        count=8,
    ),
)
~~~

Daily, weekly, monthly, and yearly recurrence are supported.

## 11. Cancel and reschedule

Cancel:

~~~python
engine.cancel(booking.booking_id)
~~~

Reschedule:

~~~python
new_slot = generator.generate_for_date("2026-10-06")[2]

booking = engine.reschedule(
    booking.booking_id,
    new_slot,
)
~~~

## 12. Build an API around it

A typical Django/DRF flow is:

~~~text
GET /providers/123/availability
        |
        v
Load provider configuration
        |
        v
Create SlotGenerator
        |
        v
Create AvailabilityEngine
        |
        v
engine.available_slots(...)
        |
        v
Return JSON to frontend
        |
        v
User chooses a slot
        |
        v
POST /bookings
        |
        v
engine.reserve(slot)
        |
        +--> BookingConflictError
        |    retry/show another slot
        |
        +--> Booking
~~~

See [Django / DRF](django.md) for an application example.

## 13. Production storage

The included InMemoryBookingStore and InMemoryHoldStore are useful for learning, tests, prototypes, and simple single-process applications.

Do **not** treat them as a shared database for multiple workers.

For a real multi-worker deployment, implement BookingStore and HoldStore against your database. The final reservation must be atomic so competing requests cannot both win the same capacity.

See [Testing & Production](testing.md).

## Mental model

~~~text
Schedule
   ↓
SlotGenerator
   ↓
AvailabilityEngine
   ↓
Booking / Hold
~~~

### Schedule

Defines when a resource normally works and its exceptions.

### SlotGenerator

Turns those rules into concrete time slots.

### AvailabilityEngine

Applies current bookings, capacity, resources, policies, holds, and conflicts.

### Booking / Hold

Represents a confirmed reservation or temporary checkout reservation.

## What Slotify does not own

Keep these concerns in your application:

- users and authentication
- permissions
- customer records
- payments
- emails/SMS/WhatsApp
- frontend/UI
- your main database models
- business-specific reporting

## Where to go next

- [Concepts](concepts.md)
- [Configuration](configuration.md)
- [Availability & Booking](booking.md)
- [Recipes](recipes.md)
- [Django / DRF](django.md)
- [Timezone & DST](timezones.md)
- [Testing & Production](testing.md)
- [API Guide](api.md)
