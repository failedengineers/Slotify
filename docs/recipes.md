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

available = engine.available_slots("2026-09-21")

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
