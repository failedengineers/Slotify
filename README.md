# Slotify Scheduling

A timezone-aware Python scheduling and appointment slot engine.

Slotify generates appointment slots from simple schedules while handling timezones, daylight-saving transitions, breaks, exclusions, booking policies, capacity, and reservations.

## Installation

```bash
pip install slotify-scheduling
```

The Python package is imported as:

```python
from slotify import SlotGenerator
```

## Basic usage

```python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate(
    "2026-09-21",
    "2026-09-25",
)

for slot in slots:
    print(slot.start, slot.end)
```

## Weekly schedules

Different days can have different working hours.

```python
from slotify import Schedule, SlotGenerator

schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "tuesday": [("09:00", "17:00")],
        "wednesday": [("12:00", "20:00")],
        "thursday": [("09:00", "17:00")],
        "friday": [("09:00", "14:00")],
        "saturday": [("10:00", "13:00")],
    }
)

generator = SlotGenerator(
    schedule=schedule,
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate(
    "2026-09-21",
    "2026-09-27",
)
```

## Date overrides

A specific date can replace the normal weekly schedule.

```python
schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
    },
    overrides={
        "2026-09-21": [("13:00", "18:00")],
        "2026-09-28": [],
    },
)
```

An empty override closes that date.

## Holidays and recurring closures

```python
schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "friday": [("09:00", "17:00")],
    },
    closed_dates=[
        "2026-10-02",
    ],
    annual_closed_dates=[
        "12-25",
        "01-01",
    ],
)
```

Explicit closures take priority over schedule overrides.

## Multiple windows and breaks

```python
generator = SlotGenerator(
    windows=[
        ("09:00", "13:00"),
        ("14:00", "18:00"),
    ],
    breaks=[
        ("11:00", "11:30"),
    ],
    duration=30,
    timezone="Asia/Kolkata",
)
```

## Timezones and DST

Use an IANA timezone:

```python
generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="America/New_York",
)
```

Slotify uses Python's timezone support and keeps slot calculations based on real timezone-aware instants.

DST behavior can be configured:

```python
generator = SlotGenerator(
    start="01:00",
    end="03:00",
    duration=30,
    timezone="America/New_York",
    dst_ambiguous="raise",
    dst_nonexistent="skip",
)
```

Supported ambiguous-time policies are:

```text
raise
earlier
later
both
```

Supported nonexistent-time policies are:

```text
raise
skip
```

## Rolling availability

Generate upcoming slots relative to a specific current time:

```python
from datetime import datetime

slots = generator.upcoming(
    7,
    now=datetime.fromisoformat(
        "2026-09-21T08:00:00+05:30"
    ),
)
```

Passing `now` explicitly also makes application tests deterministic.

## Booking and availability

Slotify separates slot generation from booking.

```python
from slotify import (
    AvailabilityEngine,
    SlotGenerator,
)

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

available = engine.available_slots(
    "2026-09-21",
)

booking = engine.reserve(
    available[0],
)
```

Cancel a booking:

```python
engine.cancel(
    booking.booking_id,
)
```

## Booking buffers

Buffers can prevent immediately adjacent appointments from being booked.

```python
engine = AvailabilityEngine(
    generator,
    buffer_before=10,
    buffer_after=15,
)
```

This protects the booking interval before and after the actual appointment.

## Capacity

Multiple reservations can be allowed for the same slot:

```python
engine = AvailabilityEngine(
    generator,
    capacity=3,
)
```

The included `InMemoryBookingStore` is useful for testing and single-process applications.

For multi-process or distributed deployments, applications should provide a `BookingStore` implementation backed by their database or other transactional storage system.

## Booking policies

Minimum notice and maximum booking horizon can be configured:

```python
from datetime import timedelta

from slotify import BookingPolicy

policy = BookingPolicy(
    minimum_notice=timedelta(hours=2),
    maximum_horizon=timedelta(days=30),
)
```

Blocked periods can also be defined:

```python
from datetime import datetime

from slotify import (
    BlockedPeriod,
    BookingPolicy,
)

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
```

Then pass the policy to the availability engine:

```python
engine = AvailabilityEngine(
    generator,
    policy=policy,
)
```

## API overview

### `SlotGenerator`

Generates slots from scheduling rules.

```text
generate()
generate_for_date()
upcoming()
```

### `Schedule`

Defines:

```text
weekly schedules
date overrides
closed dates
annual recurring closures
```

### `Slot`

Represents one immutable appointment interval.

```text
start
end
duration
start_utc
end_utc
overlaps()
contains()
in_timezone()
to_dict()
```

### `AvailabilityEngine`

Handles:

```text
availability
capacity
buffers
booking policies
reservations
cancellation
```

### `Booking`

Represents a reservation and its protected time interval.

## Requirements

* Python 3.10+
* No third-party runtime dependency on Linux/macOS
* `tzdata` is installed automatically on Windows

## Project status

Slotify is actively developed. The API may evolve before the first stable `1.0.0` release.

Current development version:

```text
0.1.0
```

## License

Slotify is released under the MIT License.

## Author

Kalash Gulati
