# Resource Pools

Use a resource pool when a booking can be handled by any one member of a group.

Examples: doctors, stylists, trainers, rooms, or support agents.

## Basic pool

~~~python
engine = AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2", "doctor-3"),
)

booking = engine.reserve(slot)
print(booking.resource_id)
~~~

## Selection strategies

### first_available

Default. Checks resources in the configured order.

~~~python
AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2"),
    resource_strategy="first_available",
)
~~~

### round_robin

Rotates the starting resource.

~~~python
AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2"),
    resource_strategy="round_robin",
)
~~~

### least_loaded

Prefers the resource with fewer overlapping confirmed bookings.

~~~python
AvailabilityEngine(
    generator,
    resource_pool=("doctor-1", "doctor-2"),
    resource_strategy="least_loaded",
)
~~~

These strategies are allocation helpers. Your application should still filter resources based on qualifications, service, location, branch, or other business rules.

## Production concurrency

Resource selection does not replace concurrency control.

Two requests can observe the same resource as available. The final reservation in your BookingStore must be atomic.


## Required resources

For appointments that require multiple resources together, use resource_ids:

~~~python
AvailabilityEngine(
    generator,
    resource_ids=("doctor-1", "room-4"),
)
~~~

A booking protects all listed resources. Another booking conflicts when its protected interval overlaps and it shares at least one required resource. This provides the core availability intersection needed for provider + room + equipment style appointments.
