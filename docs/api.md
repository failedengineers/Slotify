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
reserve()
cancel()
capacity
buffers
booking policies
resource_id
~~~

## Booking

Represents a reservation and its protected time interval.

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
    Schedule,
    Slot,
    SlotGenerator,
    TimeWindow,
)
~~~
