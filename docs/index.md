# Slotify Scheduling

**Timezone-aware scheduling and appointment slot engine for Python.**

Slotify is the scheduling layer underneath appointment and resource-booking applications.

## Install

~~~bash
pip install slotify-scheduling
~~~

## Start here

If you just want to build something:

**[→ Build Your First Booking System](build-your-first-booking.md)**

If you want the basics first:

**[→ Getting Started](getting-started.md)**

## 60-second example

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

## What Slotify handles

- working schedules
- breaks and closures
- timezones and DST
- availability
- capacity
- resources and resource pools
- booking policies
- holds
- reservations
- cancellation and rescheduling
- recurring bookings
- iCalendar export

## What your application handles

- users and authentication
- customer/provider models
- payments
- notifications
- frontend/UI
- HTTP/API
- database persistence

## How it fits

~~~text
Your application
       ↓
Scheduling service
       ↓
SlotGenerator
       ↓
AvailabilityEngine
       ↓
BookingStore / HoldStore
       ↓
Your database
~~~

## Choose what you need

| Goal | Start here |
|---|---|
| I am completely new | Getting Started |
| I need a booking system | Build Your First Booking System |
| I need normal working hours | Configuration |
| I need availability | Availability & Booking |
| I need checkout holds | Temporary Holds |
| I have multiple providers | Resource Pools |
| I use Django / DRF | Django / DRF |
| I need timezone/DST help | Timezones & DST |
| I want API details | API Guide |
| I am deploying | Testing & Production |
| I need runnable code | Runnable Examples |

## Common use cases

Doctor appointments, therapists, consultants, salons, trainers, classes, interviews, rooms, equipment, and staff/resource scheduling.

## Links

- [PyPI](https://pypi.org/project/slotify-scheduling/)
- [GitHub](https://github.com/failedengineers/Slotify)
- [Issues](https://github.com/failedengineers/Slotify/issues)
