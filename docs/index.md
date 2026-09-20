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
- reservations and cancellation

Slotify keeps these scheduling rules in one Python layer.

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

**New to Slotify?** Start with [Getting Started](getting-started.md).

**Using Django?** Go to [Django Integration](django.md).

**Working across timezones?** Read [Timezone & DST](timezones.md).

**Looking for copy-paste patterns?** See [Recipes](recipes.md).

**Need the public API map?** See [API Guide](api.md).

## Project links

- [PyPI](https://pypi.org/project/slotify-scheduling/)
- [GitHub](https://github.com/failedengineers/Slotify)
- [Issues](https://github.com/failedengineers/Slotify/issues)
