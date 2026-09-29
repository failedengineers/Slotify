# Recipes

## Doctor / therapist appointments

~~~python
from slotify import AvailabilityEngine, SlotGenerator

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

available = engine.available_slots("2026-10-21")

if available:
    booking = engine.reserve(available[0])
~~~

## Group class

~~~python
engine = AvailabilityEngine(
    generator,
    resource_id="yoga-class-1",
    capacity=10,
)
~~~

## Lunch break

~~~python
generator = SlotGenerator(
    start="09:00",
    end="18:00",
    duration=30,
    breaks=[("13:00", "14:00")],
    timezone="Asia/Kolkata",
)
~~~

## Split shift

~~~python
generator = SlotGenerator(
    windows=[
        ("09:00", "13:00"),
        ("14:00", "18:00"),
    ],
    duration=30,
    timezone="Asia/Kolkata",
)
~~~

## Closed holiday

~~~python
schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
    },
    annual_closed_dates=["12-25"],
)
~~~

## One-off closure

~~~python
schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
    },
    overrides={
        "2026-10-12": [],
    },
)
~~~

## Preparation time

~~~python
engine = AvailabilityEngine(
    generator,
    buffer_before=10,
    buffer_after=15,
)
~~~

## Booking notice and horizon

~~~python
from datetime import timedelta
from slotify import BookingPolicy

policy = BookingPolicy(
    minimum_notice=timedelta(hours=2),
    maximum_horizon=timedelta(days=30),
)
~~~

## Provider unavailable for a period

~~~python
from datetime import datetime
from slotify import BlockedPeriod, BookingPolicy

policy = BookingPolicy(
    blocked_periods=(
        BlockedPeriod(
            start=datetime.fromisoformat(
                "2026-10-10T10:00:00+05:30"
            ),
            end=datetime.fromisoformat(
                "2026-10-10T14:00:00+05:30"
            ),
            reason="Provider unavailable",
        ),
    ),
)
~~~


## Recurring appointments

~~~python
from slotify import RecurrenceRule

rule = RecurrenceRule(
    weekdays=(0,),
    count=8,
)

bookings = engine.reserve_recurring(
    template_slot,
    rule,
)
~~~

If one occurrence cannot be booked, Slotify rolls back occurrences already created by that series.

## Rescheduling

~~~python
booking = engine.reschedule(
    booking.booking_id,
    new_slot,
)
~~~

Rescheduling keeps the same booking ID and increments rescheduled_count.

## Multiple resources

Use multiple resources when an appointment requires more than one resource, such as a doctor and a room.

~~~python
engine = AvailabilityEngine(
    generator,
    resource_ids=("doctor-1", "room-1"),
)
~~~

Two bookings conflict when their protected intervals overlap and they share at least one resource.

## Calendar export

~~~python
ics = booking.to_ics(
    summary="Consultation",
    description="Patient consultation",
    location="Room 1",
)
~~~

Write the returned text to an .ics file or return it from your web application.
