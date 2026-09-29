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

## Current focus

- Keep scheduling behavior predictable and timezone-safe.
- Expand DST and recurrence edge-case coverage.
- Improve database-backed BookingStore examples.
- Add performance benchmarks for large availability ranges.
- Collect real-world scheduling use cases and bug reports.

## Exploring

- PostgreSQL/SQLAlchemy BookingStore examples
- Calendar conflict adapters
- Additional framework examples
- Performance improvements for large resource pools
- More advanced routing and resource-selection strategies

## Scope

Slotify intentionally does not provide users, authentication, payments, notifications, hosted booking pages, or a frontend. Those remain application-level concerns.
