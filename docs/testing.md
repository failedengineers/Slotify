# Testing & Production

## Install

~~~bash
python -m pip install slotify-scheduling
python -m pip install pytest
~~~

Check the installed version:

~~~bash
python -c "import slotify; print(slotify.__version__)"
~~~

Expected for this documentation release:

~~~text
0.5.1
~~~

## Run your tests

~~~bash
python -m pytest
~~~

## Deterministic time tests

upcoming() and availability checks can depend on the current time.

Pass an explicit timezone-aware now value:

~~~python
from datetime import datetime

slots = generator.upcoming(
    7,
    now=datetime.fromisoformat(
        "2026-10-05T08:00:00+05:30"
    ),
)
~~~

This prevents tests from changing simply because the real clock moved.

## Test conflicts

~~~python
import pytest
from slotify import BookingConflictError

slot = generator.generate_for_date("2026-10-05")[0]

engine.reserve(slot)

with pytest.raises(BookingConflictError):
    engine.reserve(slot)
~~~

For capacity greater than one, reserve up to the configured capacity before asserting that the next reservation fails.

## Test cancellation

~~~python
booking = engine.reserve(slot)

cancelled = engine.cancel(
    booking.booking_id,
)

assert cancelled.status == "cancelled"
~~~

## Test rescheduling

~~~python
booking = engine.reserve(slot)

new_slot = generator.generate_for_date("2026-10-06")[0]

updated = engine.reschedule(
    booking.booking_id,
    new_slot,
)

assert updated.booking_id == booking.booking_id
assert updated.rescheduled_count == 1
~~~

## Test recurring rollback

A recurring reservation is intended to be all-or-nothing.

Create a rule where a later occurrence cannot be matched or booked, then assert that the earlier occurrences created by that series have been cancelled.

## Test DST-sensitive applications

For supported timezones, test:

~~~text
normal local times
spring-forward transition
fall-back transition
timezone conversion
UTC serialization
~~~

Use explicit dates so the tests remain reproducible.

## Production storage

InMemoryBookingStore is thread-safe within one process, but it is not a distributed database.

Good uses:

~~~text
unit tests
local development
simple single-process services
~~~

For a multi-worker or multi-instance web application, provide a durable database-backed BookingStore.

Your implementation should make reserve() and reschedule() atomic in the underlying database so concurrent requests cannot both consume the same capacity.

## Production architecture

~~~text
Application
├── authentication
├── users
├── providers/resources
├── payments
├── notifications
├── database
└── Slotify
     ├── schedules
     ├── slot generation
     ├── availability
     ├── booking policy
     └── conflict checks
~~~

## Store business timezones explicitly

A provider should have a timezone field:

~~~python
provider_timezone = "Asia/Kolkata"
~~~

Pass that timezone into SlotGenerator.

Do not rely on the server's local timezone for provider business rules.

## Handle exceptions at the application boundary

~~~python
from slotify import (
    BookingConflictError,
    SlotUnavailableError,
)

try:
    booking = engine.reserve(slot)
except BookingConflictError:
    # Another request may have taken the slot.
    ...
except SlotUnavailableError:
    # The slot violates the configured booking rules.
    ...
~~~

Return user-friendly application responses rather than exposing Python tracebacks.

## Version pinning

Slotify is currently in alpha.

For production, pin the version that you have tested:

~~~text
slotify-scheduling==0.5.1
~~~

Review the changelog before upgrading.

## Windows timezone data

On Windows, Slotify declares tzdata automatically as a runtime dependency.

Linux and macOS normally use their system timezone database.

## Release checklist for an application

Before deploying a system built with Slotify, verify:

~~~text
[ ] provider timezones are stored
[ ] business hours are tested
[ ] DST cases are tested where applicable
[ ] capacity rules are tested
[ ] cancellation/reschedule rules are tested
[ ] concurrent booking behavior is safe
[ ] durable booking storage is configured
[ ] application authentication is enforced
[ ] payment and notification logic is outside Slotify
[ ] package version is pinned
~~~


## External calendar conflicts

Test BusyPeriod values from Google Calendar, Outlook, your own calendar service, or another source as ordinary scheduling conflicts. Keep the external adapter in your application and pass normalized BusyPeriod objects into Slotify.

## Idempotency

For retried HTTP/payment requests, test that the same idempotency key returns the same Booking and that different keys still obey normal conflict rules.

## Availability diagnostics

Use AvailabilityResult.code for API-level error handling and AvailabilityResult.reason for logs or user-facing explanations.
