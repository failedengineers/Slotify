# Build Your First Booking System

This guide is for developers who want to build a real booking flow.

## The flow

~~~text
Working hours
    ↓
Generate slots
    ↓
Show availability
    ↓
Customer selects
    ↓
Reserve
    ↓
Confirm / cancel / reschedule
~~~

Slotify handles scheduling. Your application handles users, authentication, payments, database models, HTTP, and UI.

## 1. Install

~~~bash
pip install slotify-scheduling
~~~

## 2. Create the scheduler

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)
~~~

## 3. Make it bookable

~~~python
from slotify import AvailabilityEngine

engine = AvailabilityEngine(
    generator,
    resource_id="doctor-123",
    capacity=1,
)

slots = engine.available_slots("2026-10-05")
booking = engine.reserve(slots[0])
~~~

If another request has already taken the slot, reserve raises BookingConflictError.

~~~python
from slotify import BookingConflictError

try:
    booking = engine.reserve(selected_slot)
except BookingConflictError:
    return {"error": "That slot was just booked. Please choose another."}
~~~

## 4. Add booking rules

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
    resource_id="doctor-123",
    policy=policy,
)
~~~

## 5. Add breaks and holidays

~~~python
generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    breaks=[("13:00", "14:00")],
    timezone="Asia/Kolkata",
)
~~~

For weekly hours and closures:

~~~python
from slotify import Schedule

schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "tuesday": [("09:00", "17:00")],
        "wednesday": [("09:00", "17:00")],
        "thursday": [("09:00", "17:00")],
        "friday": [("09:00", "17:00")],
    },
    closed_dates=["2026-10-02"],
)
~~~

## 6. Hold during checkout

~~~python
from datetime import datetime

hold = engine.hold(
    selected_slot,
    expires_at=datetime.fromisoformat("2026-10-05T09:10:00+05:30"),
)

# after successful payment
booking = engine.confirm_hold(hold.hold_id)

# if checkout is abandoned
engine.release_hold(hold.hold_id)
~~~

A hold is a temporary scheduling claim. It is not payment confirmation.

## 7. Cancel and reschedule

~~~python
engine.cancel(booking.booking_id)

new_slot = engine.available_slots("2026-10-06")[0]
booking = engine.reschedule(booking.booking_id, new_slot)
~~~

## 8. Multiple providers

If any provider can handle the appointment:

~~~python
engine = AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2", "doctor-3"),
    resource_strategy="least_loaded",
)
~~~

## 9. Django / DRF architecture

Keep your normal application models:

~~~text
Provider
Customer
Booking
Payment
Service
~~~

Put Slotify in your service layer:

~~~text
Django request
    ↓
View / API
    ↓
Scheduling service
    ↓
SlotGenerator
    ↓
AvailabilityEngine
    ↓
BookingStore
    ↓
Database
~~~

See the Django integration guide.

## The production rule that matters most

Availability shown to a customer is not a guarantee.

Between checking availability and creating the booking, another customer can book the same slot.

Your final reservation must therefore be atomic in your database store.

~~~text
show availability
       ↓
customer selects
       ↓
attempt atomic reservation
       ↓
success → confirmation
failure → refresh availability
~~~

## Which API should I use?

| I need to... | Use |
|---|---|
| Generate normal slots | SlotGenerator.generate() |
| Generate one date | generate_for_date() |
| Get bookable slots | available_slots() |
| Get the next slot | next_available() |
| Search a datetime range | available_between() |
| Find a slot long enough for a service | available_for_duration() |
| Check why unavailable | check_availability() |
| Reserve | reserve() |
| Reserve the first available slot | reserve_first_available() |
| Temporarily hold checkout | hold() |
| Confirm a hold | confirm_hold() |
| Cancel | cancel() |
| Reschedule | reschedule() |
| Create recurring bookings | reserve_recurring() |
| Let any provider handle it | resource_pool |
| Enforce booking limits | BookingPolicy |

## What Slotify does not own

Keep users, authentication, payments, notifications, frontend/UI, customer records, and business reporting in your application.

Slotify remains the scheduling engine underneath those systems.
