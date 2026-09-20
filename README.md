# Slotify Scheduling

**Timezone-aware scheduling and appointment slot engine for Python.**


## Installation

~~~bash
pip install slotify-scheduling
~~~

## Quick start

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

## Why Slotify?

Scheduling becomes difficult when several rules interact:

~~~text
working hours + breaks + holidays + overrides
+ timezones + DST + capacity + buffers
+ booking policies + reservations
~~~

Slotify keeps those rules in a scheduling layer while your application remains responsible for users, authentication, payments, notifications, databases, and UI.

## Common use cases

- Doctor, therapist, consultant, salon, or clinic appointments
- Meeting and interview scheduling
- Classroom and group sessions
- Rooms, equipment, staff, and other resource booking
- Availability APIs in Django, FastAPI, Flask, or other Python applications

## Features

### Weekly schedules

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

### Date overrides and closures

~~~python
schedule = Schedule(
    weekly={"monday": [("09:00", "17:00")]},
    overrides={
        "2026-09-21": [("13:00", "18:00")],
        "2026-09-28": [],
    },
    closed_dates=["2026-10-02"],
    annual_closed_dates=["12-25", "01-01"],
)
~~~

An empty override closes that date.

### Breaks and split windows

~~~python
generator = SlotGenerator(
    windows=[
        ("09:00", "13:00"),
        ("14:00", "18:00"),
    ],
    breaks=[("11:00", "11:30")],
    duration=30,
    timezone="Asia/Kolkata",
)
~~~

### Timezones and DST

~~~python
generator = SlotGenerator(
    start="01:00",
    end="03:00",
    duration=30,
    timezone="America/New_York",
    dst_ambiguous="raise",
    dst_nonexistent="skip",
)
~~~

Ambiguous policies: raise, earlier, later, both.

Nonexistent-time policies: raise, skip.

See the [Timezone & DST guide](https://failedengineers.github.io/Slotify/timezones/).

### Upcoming availability

~~~python
from datetime import datetime

slots = generator.upcoming(
    7,
    now=datetime.fromisoformat("2026-09-21T08:00:00+05:30"),
)
~~~

Passing now explicitly makes tests deterministic.

### Booking and capacity

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

available = engine.available_slots("2026-09-21")

if available:
    booking = engine.reserve(available[0])
    print(booking.booking_id)
~~~

Cancel with engine.cancel(booking.booking_id).

For group sessions, use a larger capacity.

~~~python
engine = AvailabilityEngine(
    generator,
    resource_id="class-1",
    capacity=10,
)
~~~

### Booking buffers

~~~python
engine = AvailabilityEngine(
    generator,
    buffer_before=10,
    buffer_after=15,
)
~~~

Useful for setup, cleanup, travel, or preparation time.

### Booking policies

~~~python
from datetime import timedelta
from slotify import BookingPolicy

policy = BookingPolicy(
    minimum_notice=timedelta(hours=2),
    maximum_horizon=timedelta(days=30),
)
~~~

Blocked periods:

~~~python
from datetime import datetime
from slotify import BlockedPeriod, BookingPolicy

policy = BookingPolicy(
    blocked_periods=(
        BlockedPeriod(
            start=datetime.fromisoformat("2026-10-10T10:00:00+05:30"),
            end=datetime.fromisoformat("2026-10-10T14:00:00+05:30"),
            reason="Provider unavailable",
        ),
    ),
)
~~~

## Django

Slotify can sit behind a Django or Django REST Framework endpoint.

~~~bash
pip install slotify-scheduling
~~~

Example service:

~~~python
from slotify import AvailabilityEngine, SlotGenerator

def get_provider_engine(provider):
    generator = SlotGenerator(
        start=provider.work_start.strftime("%H:%M"),
        end=provider.work_end.strftime("%H:%M"),
        duration=provider.slot_duration,
        timezone=provider.timezone,
    )

    return AvailabilityEngine(
        generator,
        resource_id=str(provider.pk),
        capacity=1,
    )
~~~

Example view:

~~~python
from django.http import JsonResponse
from .models import Provider
from .services import get_provider_engine

def available_slots(request, provider_id):
    provider = Provider.objects.get(pk=provider_id)
    engine = get_provider_engine(provider)

    slots = engine.available_slots("2026-09-21")

    return JsonResponse({
        "provider_id": provider.pk,
        "slots": [slot.to_dict() for slot in slots],
    })
~~~

**Production note:** the built-in InMemoryBookingStore is for tests and simple single-process applications. Multi-worker or distributed Django deployments should provide a database-backed BookingStore and enforce the required transaction/concurrency rules in the application's database layer.

## Architecture

~~~text
Your Django/FastAPI/etc. application
├── users and authentication
├── providers/resources
├── database
├── payments
├── notifications
└── frontend/API
          |
          v
       Slotify
       ├── Schedule
       ├── SlotGenerator
       ├── Slot
       ├── AvailabilityEngine
       ├── BookingPolicy
       └── Booking
~~~

## Documentation

- [Documentation home](https://failedengineers.github.io/Slotify/)
- [Getting Started](https://failedengineers.github.io/Slotify/getting-started/)
- [Django / DRF](https://failedengineers.github.io/Slotify/django/)
- [Timezone & DST](https://failedengineers.github.io/Slotify/timezones/)
- [Recipes](https://failedengineers.github.io/Slotify/recipes/)
- [API Guide](https://failedengineers.github.io/Slotify/api/)

## Community

- [Contributing](CONTRIBUTING.md)
- [Roadmap](ROADMAP.md)
- [Support](SUPPORT.md)
- [Security](SECURITY.md)

## Requirements

- Python 3.10+
- No third-party runtime dependency on Linux/macOS
- tzdata is installed automatically on Windows

## Project status

Current version: **0.1.2**

Slotify is currently in alpha. The API may evolve before 1.0.0, so pin the version in production applications and review the changelog when upgrading.

## License

MIT License

## Author

Kalash Gulati
