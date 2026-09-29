# Performance Benchmarks

Slotify should be measured with the scheduling configuration your application actually uses.

A useful benchmark should vary:

- number of days scanned
- slots per day
- number of resources
- number of existing bookings
- number of holds
- timezone/DST complexity

## Simple local benchmark

The following measures a repeated availability query without adding a benchmark dependency:

~~~python
from time import perf_counter
from slotify import AvailabilityEngine, SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)
engine = AvailabilityEngine(generator)

start = perf_counter()
for _ in range(100):
    engine.available_slots("2026-10-05", "2026-10-30")
elapsed = perf_counter() - start

print(f"{elapsed:.4f}s for 100 queries")
~~~

Treat this as a smoke benchmark, not a universal performance claim. Production performance depends heavily on the application store, resource count, database, and workload.
