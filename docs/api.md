# API Guide

This is the user-facing map of the public API.

## SlotGenerator

Turns scheduling rules into appointment slots.

Common operations:

~~~text
generate()
generate_for_date()
upcoming()
~~~

## Schedule

Defines recurring availability and exceptions:

~~~text
weekly
overrides
closed_dates
annual_closed_dates
~~~

## Slot

Represents an immutable appointment interval.

Common attributes and methods:

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

Adds booking-aware behavior:

~~~text
availability
capacity
buffers
booking policies
reservations
cancellation
~~~

## Booking

Represents a reservation and its protected interval.

## BookingPolicy

Defines constraints such as minimum notice, maximum horizon, and blocked periods.

## Storage

The included InMemoryBookingStore is useful for tests and simple single-process applications.

For multi-process or distributed applications, use a BookingStore backed by transactional application storage.

For exact signatures, use the version of the package installed in your environment as the source of truth.
