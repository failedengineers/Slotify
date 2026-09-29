# Availability & Booking

This guide shows the full booking workflow.

## 1. Create the schedule

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)
~~~

## 2. Create the availability engine

~~~python
from slotify import AvailabilityEngine

engine = AvailabilityEngine(
    generator,
    resource_id="doctor-123",
    capacity=1,
)
~~~

## 3. Get bookable slots

~~~python
available = engine.available_slots("2026-10-05")

for slot in available[:5]:
    print(slot.start, "->", slot.end)
~~~

available_slots() starts with generated slots and filters them using booking policy, existing bookings, capacity, resources, and buffers.

## Check a single slot

~~~python
if engine.is_available(slot):
    print("The slot is currently available")
~~~

Availability may change before the final reservation, so the application should treat reserve() as the final booking operation.

## 4. Reserve

~~~python
booking = engine.reserve(
    slot,
    metadata={
        "customer_id": "user-42",
        "service": "consultation",
    },
)

print(booking.booking_id)
~~~

Metadata is returned by booking.to_dict().

## 5. Reserve the first available appointment

~~~python
booking = engine.reserve_first_available(
    "2026-10-05",
    "2026-10-09",
    metadata={"customer_id": "user-42"},
)
~~~

This tries available slots until one is successfully reserved.

## Capacity

One-person appointment:

~~~python
engine = AvailabilityEngine(
    generator,
    resource_id="doctor-123",
    capacity=1,
)
~~~

Ten-person class:

~~~python
engine = AvailabilityEngine(
    generator,
    resource_id="class-1",
    capacity=10,
)
~~~

The included in-memory store tracks overlapping confirmed bookings against the configured capacity.

## Multiple resources

Use resource_ids when one appointment needs multiple resources.

~~~python
engine = AvailabilityEngine(
    generator,
    resource_ids=("doctor-123", "room-4"),
)
~~~

An overlapping booking conflicts when it shares at least one resource.

This fits cases such as:

~~~text
doctor + room
barber + chair
technician + machine
trainer + studio
~~~

## Buffers

~~~python
engine = AvailabilityEngine(
    generator,
    resource_id="chair-2",
    buffer_before=10,
    buffer_after=15,
)
~~~

Buffers do not change the appointment's displayed start/end. They expand the protected interval used for conflicts.

## Booking policies

~~~python
from datetime import timedelta
from slotify import AvailabilityEngine, BookingPolicy

policy = BookingPolicy(
    minimum_notice=timedelta(hours=2),
    maximum_horizon=timedelta(days=30),
    cancellation_window=timedelta(hours=12),
    reschedule_window=timedelta(hours=6),
    max_reschedules=2,
)

engine = AvailabilityEngine(
    generator,
    resource_id="doctor-123",
    capacity=1,
    policy=policy,
)
~~~

### Minimum notice

minimum_notice prevents booking too close to the current time.

~~~python
minimum_notice=timedelta(hours=2)
~~~

### Maximum horizon

maximum_horizon prevents booking too far into the future.

~~~python
maximum_horizon=timedelta(days=30)
~~~

### Blocked periods

~~~python
from datetime import datetime
from slotify import BlockedPeriod, BookingPolicy

policy = BookingPolicy(
    blocked_periods=(
        BlockedPeriod(
            start=datetime.fromisoformat("2026-10-10T10:00:00+05:30"),
            end=datetime.fromisoformat("2026-10-10T14:00:00+05:30"),
            reason="Doctor on leave",
        ),
    ),
)
~~~

Any overlapping slot is rejected by the policy.

## Cancellation

Cancel by booking ID.

~~~python
cancelled = engine.cancel(booking.booking_id)
print(cancelled.status)
~~~

The resulting status is cancelled.

An already-cancelled booking can be cancelled again safely through the engine.

A cancellation window can prevent last-minute cancellation:

~~~python
BookingPolicy(
    cancellation_window=timedelta(hours=12),
)
~~~

## Rescheduling

Generate a target slot, then reschedule the existing booking.

~~~python
new_slot = generator.generate_for_date("2026-10-06")[3]

updated = engine.reschedule(
    booking.booking_id,
    new_slot,
)

print(updated.booking_id)
print(updated.rescheduled_count)
~~~

The booking ID stays the same and rescheduled_count increases.

The new slot is checked against policy, capacity, resources, and conflicts.

Cancelled bookings cannot be rescheduled.

## Recurring bookings

Create a weekly series from a template slot.

~~~python
from slotify import RecurrenceRule

template_slot = generator.generate_for_date("2026-10-05")[0]

rule = RecurrenceRule(
    weekdays=(0,),
    count=8,
)

series = engine.reserve_recurring(
    template_slot,
    rule,
)
~~~

Python weekday numbering is Monday=0 through Sunday=6.

Every-two-weeks example:

~~~python
rule = RecurrenceRule(
    weekdays=(0,),
    interval=2,
    count=6,
)
~~~

Stop at a date:

~~~python
rule = RecurrenceRule(
    weekdays=(0,),
    until="2026-12-28",
)
~~~

count and until cannot be used together.

Every booking in a series receives the same series_id.

If an occurrence cannot be reserved, occurrences already created by that series are cancelled before the error is returned.

## Upcoming availability

For a rolling list of bookable future slots:

~~~python
from datetime import datetime

available = engine.upcoming_available(
    7,
    now=datetime.fromisoformat("2026-10-05T08:00:00+05:30"),
)
~~~

Pass now explicitly for deterministic tests.

## List bookings

Use the store to inspect bookings:

~~~python
bookings = engine.store.list(
    resource_id="doctor-123",
)
~~~

Filter a recurring series:

~~~python
series_bookings = engine.store.list(
    series_id=booking.series_id,
)
~~~

Cancelled bookings are excluded by default.

Include them explicitly:

~~~python
all_bookings = engine.store.list(
    include_cancelled=True,
)
~~~

## iCalendar export

Export a booking to iCalendar text:

~~~python
ics_text = booking.to_ics(
    summary="Doctor Appointment",
    description="30-minute consultation",
    location="Room 4",
)
~~~

Your application can return the string as an .ics response or save it as a calendar file.

## Recommended web request flow

~~~text
GET /providers/123/availability
        |
        v
Django/DRF loads provider settings
        |
        v
SlotGenerator + AvailabilityEngine
        |
        v
Return available slots
        |
        v
User selects a slot
        |
        v
POST /bookings
        |
        v
reserve(slot)
        |
        +--> BookingConflictError
        |       if another request won the race
        |
        +--> Booking
~~~

Keep authentication, payments, notifications, and database records in your application.
