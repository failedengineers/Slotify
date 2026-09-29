# Migrating to v0.4.0

Version 0.2.0 adds booking features while keeping the core slot-generation model.

## Existing slot generation

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(start="09:00", end="17:00", duration=30, timezone="Asia/Kolkata")
slots = generator.generate_for_date("2026-10-05")
~~~

## Main additions

~~~text
AvailabilityEngine.upcoming_available()
AvailabilityEngine.reserve_recurring()
AvailabilityEngine.cancel()
AvailabilityEngine.reschedule()
RecurrenceRule
cancellation/rescheduling policy fields
multi-resource bookings
iCalendar export
resource-aware conflict checks
~~~

## Recurring bookings

~~~python
from slotify import RecurrenceRule

rule = RecurrenceRule(weekdays=(0,), count=8)
series = engine.reserve_recurring(template_slot, rule)
~~~

## Stable booking IDs

Rescheduling keeps the existing booking_id and increments rescheduled_count.

## Multiple resources

Single-resource code continues to use resource_id. Multi-resource appointments can use resource_ids:

~~~python
resource_ids=("doctor-123", "room-4")
~~~

## Calendar export

~~~python
ics_text = booking.to_ics(summary="Consultation")
~~~

## Storage

InMemoryBookingStore remains useful for tests and simple single-process services. Multi-worker production systems should provide a durable database-backed BookingStore with atomic reservation behavior.

## Check the installed version

~~~bash
python -c "import slotify; print(slotify.__version__)"
~~~

Expected: 0.2.0.

See the Changelog for release details.
