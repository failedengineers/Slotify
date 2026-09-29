# Database-backed Stores

Slotify deliberately does not require Django, SQLAlchemy, or a database. The core package defines the BookingStore protocol so your application can choose its persistence layer.

## Production rule

The final reservation must be atomic in your database.

For PostgreSQL, a production store normally uses a transaction plus database-level protection for the booking/resource/time interval. The exact implementation depends on your schema and whether you use Django ORM, SQLAlchemy, or another database layer.

Your store should implement:

~~~python
class MyBookingStore:
    def reserve(self, booking):
        # transaction + database conflict protection
        ...
~~~

## Django

Keep Slotify objects at the service boundary:

~~~python
def reserve_slot(provider, slot):
    engine = get_provider_engine(provider)
    return engine.reserve(slot, idempotency_key="checkout-123")
~~~

Persist the returned Booking in your Django model inside the same application-level transaction strategy used by your store.

## SQLAlchemy

The same design works with SQLAlchemy:

~~~python
class SQLAlchemyBookingStore:
    def reserve(self, booking):
        # use Session transaction and database constraints
        ...
~~~

Slotify does not import SQLAlchemy, so applications that do not use it pay no dependency cost.

## Idempotency

Use an idempotency key for retried API requests:

~~~python
booking = engine.reserve(
    slot,
    idempotency_key=request_id,
)
~~~

The built-in in-memory store remembers the key. A database-backed store should also enforce uniqueness atomically so concurrent requests with the same key cannot create duplicates.

## Holds

The same production rule applies to HoldStore. A checkout hold and its final confirmation need shared durable storage and concurrency protection when multiple application workers can handle the same customer.
