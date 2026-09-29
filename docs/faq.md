# FAQ

## Is Slotify a complete booking platform?

No. Slotify is a Python scheduling engine.

Your application still owns users, authentication, payments, notifications, database records, permissions, and UI/API behavior.

## Do I need Django?

No.

Slotify can be used with Django, Django REST Framework, FastAPI, Flask, or another Python application.

## Does Slotify require a database?

No.

The core package works without a database.

InMemoryBookingStore is included for tests and simple single-process applications. Production systems that need durable shared state should provide a database-backed BookingStore.

## What timezone should I use?

Use the timezone of the resource being scheduled.

~~~python
timezone="Asia/Kolkata"
~~~

or:

~~~python
timezone="America/New_York"
~~~

Prefer IANA timezone names instead of hard-coded UTC offsets for recurring business schedules.

## What is the difference between duration and interval?

duration is the appointment length.

interval is the distance between generated start times.

~~~python
SlotGenerator(
    start="09:00",
    end="11:00",
    duration=30,
    interval=15,
    timezone="Asia/Kolkata",
)
~~~

This generates 30-minute appointments beginning every 15 minutes.

## Can I close a specific date?

Yes.

~~~python
Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
    },
    overrides={
        "2026-10-05": [],
    },
)
~~~

You can also use closed_dates.

## Can a window cross midnight?

Yes.

~~~python
SlotGenerator(
    windows=[("22:00", "02:00")],
    duration=60,
    timezone="Asia/Kolkata",
)
~~~

## Can one booking require several resources?

Yes.

~~~python
AvailabilityEngine(
    generator,
    resource_ids=("doctor-1", "room-1"),
)
~~~

Overlapping bookings conflict when they share at least one resource.

## Can I limit how early users can book?

Yes.

~~~python
from datetime import timedelta
from slotify import BookingPolicy

BookingPolicy(
    minimum_notice=timedelta(hours=2),
)
~~~

## Can I stop users booking too far ahead?

Yes.

~~~python
BookingPolicy(
    maximum_horizon=timedelta(days=30),
)
~~~

## Can users cancel and reschedule?

Yes.

Use engine.cancel() and engine.reschedule().

BookingPolicy can additionally limit how close to the appointment these operations are allowed and how many reschedules are permitted.

## Does rescheduling create a new booking ID?

No.

The existing booking keeps the same booking_id and increments rescheduled_count.

## Can I create recurring appointments?

Yes.

Use RecurrenceRule with engine.reserve_recurring().

## Can I export to Google Calendar or Outlook?

Slotify does not directly connect to those services.

It exports iCalendar text with booking.to_ics(). Your application can return that text as an .ics file or pass it into a calendar integration.

## Is InMemoryBookingStore safe for multiple servers?

No.

Its lock protects threads in one process. It does not provide shared distributed persistence.

Use a durable transactional store for multi-worker or multi-instance deployments.

## Why should I pass now in tests?

Because rolling availability and booking rules use the current time when now is omitted.

~~~python
from datetime import datetime

engine.upcoming_available(
    7,
    now=datetime.fromisoformat("2026-10-05T08:00:00+05:30"),
)
~~~

## Where should I start?

New users:

[Getting Started](getting-started.md)

Django applications:

[Django / DRF](django.md)

Timezone-heavy applications:

[Timezones & DST](timezones.md)

Detailed booking flows:

[Availability & Booking](booking.md)

Copy-paste patterns:

[Recipes](recipes.md)

Complete public API map:

[API Guide](api.md)
