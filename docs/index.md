# Slotify Scheduling

**Timezone-aware scheduling and appointment slot engine for Python.**

Slotify is a scheduling layer for appointment, availability, and resource-booking applications.

## Install

~~~bash
pip install slotify-scheduling
~~~

## 60-second example

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
    print(slot.start, "->", slot.end)
~~~

This creates timezone-aware 30-minute slots inside the working window.

## What Slotify solves

Real scheduling systems quickly need more than start and end times:

- recurring weekly schedules
- date-specific overrides
- holidays and closures
- multiple working windows
- breaks
- timezone-aware slots
- daylight-saving transitions
- rolling/upcoming availability
- capacity
- booking buffers
- minimum booking notice
- maximum booking horizon
- blocked periods
- reservations, cancellation, and rescheduling
- recurring appointment series
- multi-resource bookings
- booking buffers and capacity
- iCalendar (.ics) export

Slotify keeps these scheduling rules in one Python layer.

### v0.2.0 booking features

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

You can also reschedule an existing booking, apply cancellation and rescheduling rules, use multiple resources, and export a booking as iCalendar with `booking.to_ics()`.


## Where it fits

~~~text
Your application
├── users / authentication
├── providers / resources
├── database
├── payments
├── notifications
└── frontend / API
          |
          v
       Slotify
       ├── Schedule
       ├── SlotGenerator
       ├── AvailabilityEngine
       ├── BookingPolicy
       └── Booking
~~~

Slotify does **not** replace your Django/FastAPI/Flask application. It handles scheduling logic so your application can handle the rest.

## Common use cases

- doctor and therapist appointments
- consultants and coaches
- salon and service appointments
- interviews and meetings
- classes and group sessions
- rooms and equipment
- staff/resource availability
- booking APIs

## Choose your path

**New to Slotify?** Start with [Getting Started](getting-started.md), then read [Core Concepts](concepts.md).

**Using Django?** Go to [Django Integration](django.md).

**Working across timezones?** Read [Timezone & DST](timezones.md).

**Looking for configuration help?** See [Configuration](configuration.md).

**Building booking flows?** See [Availability & Booking](booking.md).

**Using Django?** See [Django / DRF](django.md).

**Looking for copy-paste patterns?** See [Recipes](recipes.md).

**Deploying to production?** Read [Testing & Production](testing.md).

**Need the public API map?** See [API Guide](api.md).

**Upgrading from 0.1.x?** Read [Migrating to v0.2.0](migration.md).

## Project links

- [PyPI](https://pypi.org/project/slotify-scheduling/)
- [GitHub](https://github.com/failedengineers/Slotify)
- [Issues](https://github.com/failedengineers/Slotify/issues)
