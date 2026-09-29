# API Guide

This page is a map of Slotify's public API. For exact signatures, the installed package version is the source of truth.

## SlotGenerator

Creates timezone-aware slots from scheduling rules.

~~~text
generate()
generate_for_date()
upcoming()
~~~

Configuration includes:

~~~text
start / end
windows
schedule
duration
interval
timezone
weekdays
breaks
excluded_dates
dst_ambiguous
dst_nonexistent
~~~

## Schedule

Defines recurring availability and exceptions.

~~~text
weekly
overrides
closed_dates
annual_closed_dates
~~~

## Slot

Represents an appointment interval.

~~~text
start
end
duration
start_utc
end_utc
overlaps()
contains()
in_timezone()
to_dict()
~~~

## AvailabilityEngine

Adds availability and booking behavior.

~~~text
available_slots()
upcoming_available()
reserve()
reserve_first_available()
reserve_recurring()
cancel()
reschedule()
capacity
buffers
booking policies
resource_id
resource_ids
~~~

## Booking

Represents a reservation and its protected time interval.

Additional v0.2.0 fields include:

~~~text
resource_ids
series_id
rescheduled_count
~~~

Useful methods include:

~~~text
cancel()
reschedule()
to_dict()
to_ics()
~~~

## RecurrenceRule

Defines weekly recurring appointment series with weekdays, interval, count, or an end date.

~~~python
RecurrenceRule(weekdays=(0, 2), count=6, interval=1)
~~~

count and until are mutually exclusive.

## BookingPolicy

Defines booking restrictions such as:

- minimum notice
- maximum booking horizon
- blocked periods

## BookingStore

The storage abstraction used by the booking layer.

Slotify includes:

~~~text
BookingStore
InMemoryBookingStore
~~~

Use the in-memory implementation for tests and simple single-process applications.

For multi-process/distributed production systems, provide durable transactional storage appropriate to your application.

## Exceptions

The package exposes scheduling and booking exceptions including:

~~~text
SlotifyError
ConfigurationError
InvalidTimeError
InvalidDateRangeError
InvalidTimezoneError
DSTTransitionError
SlotConflictError
SlotUnavailableError
BookingConflictError
BookingNotFoundError
~~~

## iCalendar export

~~~python
ics_text = booking.to_ics(summary="Doctor Appointment")
~~~

Exports a single booking as an iCalendar event without a runtime dependency.

## Timezone helpers

~~~text
get_timezone()
to_utc()
convert_timezone()
resolve_local_datetime()
~~~

## Public imports

~~~python
from slotify import (
    AvailabilityEngine,
    Booking,
    BookingPolicy,
    BookingStore,
    InMemoryBookingStore,
    RecurrenceRule,
    Schedule,
    Slot,
    SlotGenerator,
    TimeWindow,
)
~~~


## v0.3.0 availability APIs

### AvailabilityResult

check_availability() returns a structured result:

~~~python
result = engine.check_availability(slot)

result.slot
result.available
result.reason
result.resource_id
~~~

This is useful when an application needs to explain why a slot cannot be booked.

### Resource pools

Use resource_pool when an appointment can be handled by any one resource:

~~~python
AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2", "doctor-3"),
)
~~~

The selected resource is stored on the resulting Booking. resource_pool cannot be combined with resource_id or resource_ids.

### Named schedules

Multiple SlotGenerator profiles can be configured:

~~~python
AvailabilityEngine.from_schedules(
    {
        "default": default_generator,
        "evening": evening_generator,
    },
    default_schedule="default",
)
~~~

Select one per query with schedule_name. All profiles on one engine must use the same timezone.

### Availability queries

~~~python
engine.next_available(start_date, end_date=None, now=None, schedule_name=None)
engine.available_between(start_datetime, end_datetime, now=None, schedule_name=None, limit=None)
engine.available_for_duration(duration, start_date, end_date=None, now=None, schedule_name=None, limit=None)
~~~

available_between() requires timezone-aware datetimes and only returns slots fully contained in the requested interval.

available_for_duration() generates slots using the requested appointment duration while retaining the configured schedule, interval, timezone, breaks, exclusions, and DST behavior.

available_slots() and upcoming_available() also accept schedule_name and limit.

### Booking limits

BookingPolicy additionally supports:

~~~python
BookingPolicy(
    max_bookings_per_day=3,
    max_bookings_per_week=10,
    max_upcoming_bookings=5,
    min_gap_between_bookings=timedelta(minutes=15),
)
~~~

These limits are evaluated against confirmed bookings visible through the configured BookingStore.

## RecurrenceRule v0.3.0

RecurrenceRule supports daily, weekly, monthly, and yearly recurrence.

~~~python
RecurrenceRule(
    frequency="monthly",
    day_of_month=15,
    count=6,
)
~~~

Skip specific dates:

~~~python
RecurrenceRule(
    frequency="weekly",
    weekdays=(0,),
    count=12,
    excluded_dates=("2026-11-02",),
)
~~~

weekdays is valid for weekly recurrence. day_of_month is used for monthly/yearly recurrence. When a monthly day does not exist in a month, the last valid day of that month is used. count counts emitted occurrences, so excluded dates do not consume the count.
