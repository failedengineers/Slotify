# Slotify Launch Kit

## Core message

Slotify is a timezone-aware Python scheduling and appointment slot engine.

The core message is simple:

> Build scheduling and booking logic in Python without rebuilding slot generation, availability rules, timezone handling, and booking policies from scratch.

## Search/discovery themes

Use these naturally in documentation and educational posts:

- Python appointment scheduling
- Python time slot generator
- Python booking system
- Python availability engine
- Django appointment scheduling
- Django booking system
- timezone-aware scheduling Python
- daylight saving scheduling Python
- prevent appointment conflicts Python
- recurring schedule Python

## Launch post — LinkedIn

I kept running into the same problem in Python projects: appointment scheduling looks easy until you add working hours, breaks, holidays, timezones, DST, capacity, booking limits, buffers, and reservations.

So I built Slotify — a Python scheduling and appointment slot engine.

~~~bash
pip install slotify-scheduling
~~~

A simple example:

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate("2026-09-21", "2026-09-21")
~~~

It can also handle weekly schedules, date overrides, closures, breaks, DST policies, rolling availability, capacity, buffers, booking policies, reservations, and cancellation.

Docs: https://failedengineers.github.io/Slotify/
PyPI: https://pypi.org/project/slotify-scheduling/
GitHub: https://github.com/failedengineers/Slotify

Feedback and real-world use cases are welcome.

## Launch post — Reddit / developer community

I built a small Python library for the scheduling part of appointment and booking systems.

The goal was to keep scheduling rules separate from application code:

~~~text
Schedule
   ↓
SlotGenerator
   ↓
AvailabilityEngine
   ↓
Booking
~~~

It supports weekly schedules, date overrides, closures, breaks, timezones, DST behavior, capacity, buffers, booking policies, and reservations.

It also fits behind Django/DRF APIs, so your Django project can keep ownership of users, database models, payments, and notifications.

Install:

~~~bash
pip install slotify-scheduling
~~~

Project: https://github.com/failedengineers/Slotify
Docs: https://failedengineers.github.io/Slotify/

I'm especially interested in feedback from people who have built appointment or resource-booking systems.

## X / short post

Built Slotify: a timezone-aware Python scheduling engine for appointment slots.

Weekly schedules, breaks, holidays, overrides, DST, capacity, buffers, booking policies and reservations.

pip install slotify-scheduling

https://pypi.org/project/slotify-scheduling/

## Article ideas

1. How to build appointment slots in Python
2. Handling daylight-saving time in scheduling systems
3. Building appointment availability in Django
4. Why booking systems need buffers
5. Designing a timezone-aware scheduling engine
6. Building resource booking with Python
7. Separating slot generation from booking logic

## 30-day content plan

Week 1:
- Launch post
- Quick-start article
- Django integration article

Week 2:
- Timezone/DST article
- Short example showing breaks and split shifts
- GitHub discussion asking for use cases

Week 3:
- Booking policy example
- Capacity/group booking example
- Short post explaining the Schedule -> Generator -> AvailabilityEngine model

Week 4:
- Real project example
- Contributor call
- Release/changelog post

## Community strategy

Lead with useful technical content. Show the underlying scheduling problem, a small reproducible example, and how Slotify approaches it.

Avoid posting the same promotional message repeatedly. Update examples as the API evolves and turn real user questions into documentation pages.
