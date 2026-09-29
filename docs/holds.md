# Temporary Holds

Use a hold when a customer selects a slot and needs a short period to finish checkout.

~~~text
available
   ↓
hold
   ↓
payment
   ↓
confirm hold → booking
~~~

## Create

~~~python
from datetime import datetime

hold = engine.hold(
    slot,
    expires_at=datetime.fromisoformat("2026-10-05T09:10:00+05:30"),
)
~~~

## Confirm

~~~python
booking = engine.confirm_hold(hold.hold_id)
~~~

## Release

~~~python
engine.release_hold(hold.hold_id)
~~~

## Expiry

The built-in in-memory hold store ignores expired holds.

~~~python
from slotify import HoldExpiredError

try:
    engine.confirm_hold(hold.hold_id)
except HoldExpiredError:
    print("Checkout expired")
~~~

## Production

InMemoryHoldStore is intended for tests, prototypes, and simple single-process applications.

For multiple workers, implement HoldStore with shared durable storage and make the final hold/booking operation concurrency-safe.

A hold is not payment confirmation. Your payment provider remains the source of truth for payment.
