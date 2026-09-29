# Changelog

## 0.4.0

### Added
- Temporary booking holds with expiry, confirmation, and release.
- Pluggable HoldStore interface with an in-memory implementation.
- Resource-pool allocation strategies: first available, round robin, and least loaded.
- Expanded tests covering hold lifecycle, expiry, and resource selection.

### Documentation
- Reworked Getting Started as a build-first tutorial.
- Added hold and resource-strategy examples.
- Updated public API documentation.
- Switched documentation links to the custom documentation domain.


## 0.3.0 — 2026-09-29

Added:

- resource pools that select any available resource
- direct availability queries with next_available(), available_between(), and available_for_duration()
- structured AvailabilityResult explanations
- booking limits per day, week, and upcoming bookings
- minimum gap between bookings
- named availability schedules
- daily, weekly, monthly, and yearly recurrence
- recurrence date exclusions
- expanded tests and production guidance
- expanded README and API documentation

## 0.2.0 — 2026-09-29

Added:

- recurring weekly appointment series
- cancellation and rescheduling policies
- booking rescheduling with stable booking IDs
- multi-resource bookings
- iCalendar export
- upcoming bookable availability
- expanded test coverage
- expanded documentation and examples

## 0.1.2 — 2026-09-20

- Updated README documentation links to point to hosted documentation.

## 0.1.1

- Expanded README and user documentation.
- Added Django and Django REST Framework integration examples.
- Added timezone and DST guidance.
- Added recipes and API overview.
- Added package metadata and project workflows.

## 0.1.0

Initial public release with timezone-aware slot generation, schedules, overrides, closures, multiple windows, breaks, DST handling, rolling availability, capacity, booking buffers, booking policies, blocked periods, reservations, cancellation, and in-memory booking storage.
