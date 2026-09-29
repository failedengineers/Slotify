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
