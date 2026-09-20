# Getting Started

## 1. Install

~~~bash
pip install slotify-scheduling
~~~

Verify the installation:

~~~bash
python -c "import slotify; print(slotify.__version__)"
~~~

## 2. Generate your first slots

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate("2026-09-21")

for slot in slots:
    print(slot.start, "->", slot.end)
~~~

## 3. Use a weekly schedule

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

## 4. Add exceptions

~~~python
schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "friday": [("09:00", "17:00")],
    },
    overrides={
        "2026-09-21": [("13:00", "18:00")],
        "2026-09-28": [],
    },
    closed_dates=["2026-10-02"],
    annual_closed_dates=["12-25", "01-01"],
)
~~~

An empty override closes the date.

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

## 6. Generate upcoming availability

~~~python
from datetime import datetime

slots = generator.upcoming(
    7,
    now=datetime.fromisoformat("2026-09-21T08:00:00+05:30"),
)
~~~

Passing `now` explicitly is useful for deterministic tests.

## 7. Add booking

~~~python
from slotify import AvailabilityEngine

engine = AvailabilityEngine(
    generator,
    resource_id="provider-123",
    capacity=1,
)

available = engine.available_slots("2026-09-21")

if available:
    booking = engine.reserve(available[0])
    print(booking.booking_id)
~~~

Cancel:

~~~python
engine.cancel(booking.booking_id)
~~~

## Mental model

- **Schedule** — when is the resource normally available?
- **SlotGenerator** — what appointment slots exist?
- **AvailabilityEngine** — which generated slots can currently be booked?
- **BookingPolicy** — which booking times are restricted?
- **Booking** — what reservation was created?

## Production architecture

Your application should own users, permissions, payments, notifications, and durable application data.

Slotify should provide the scheduling/availability layer.

For multi-process deployments, use a database-backed `BookingStore` rather than treating `InMemoryBookingStore` as shared durable state.
