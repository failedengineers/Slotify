# Roadmap

Slotify is currently in alpha. This roadmap is a guide rather than a promise; priorities may change based on real-world usage and contributor feedback.

## v0.2.0 completed

- Recurring weekly booking series
- Cancellation and rescheduling rules
- Multi-resource booking constraints
- iCalendar export

## v0.3.0 completed

- Resource pools
- Direct availability queries
- Booking limits
- Minimum gaps between bookings
- Availability explanations
- Named availability schedules
- Daily, weekly, monthly, and yearly recurrence
- Recurrence exclusions
- Expanded tests and documentation

## v0.5.0 completed

- External busy-period conflicts
- Machine-readable availability diagnostics
- Idempotent reservation keys
- Stronger hold enforcement on direct reservations
- Database-backed store guidance
- Django, FastAPI, and Flask integration patterns
- Availability performance benchmark guidance
- Required multi-resource availability documentation

## Current focus

- Keep scheduling behavior predictable and timezone-safe.
- Expand DST, recurrence, concurrency, and store-contract coverage.
- Collect real-world scheduling use cases and bug reports.
- Measure performance with realistic workloads before optimizing.

## Exploring

- Reference PostgreSQL store implementations
- Calendar provider adapters maintained outside the core package
- Additional resource routing strategies only when real use cases require them
- Performance improvements for large resource pools

## Scope

Slotify intentionally does not provide users, authentication, payments, notifications, hosted booking pages, or a frontend. Those remain application-level concerns.
