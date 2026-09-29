## 0.2.0

- Added recurring weekly appointment series with rollback on failed occurrence.
- Added cancellation and rescheduling policies.
- Added booking rescheduling with stable booking IDs and reschedule counts.
- Added multi-resource bookings for appointments requiring shared resources.
- Added iCalendar export through Booking.to_ics().
- Added upcoming_available() to AvailabilityEngine.
- Expanded v0.2.0 test coverage.
- Updated PyPI-facing documentation and examples.

# Changelog

## 0.1.2

- Fixed README documentation links to point to the hosted documentation site.

## 0.1.1

Documentation and packaging improvements:

- Expanded README and user documentation.
- Added Django and Django REST Framework integration examples.
- Added timezone and DST guidance.
- Added recipes and API overview.
- Added project metadata for PyPI discovery.
- Added GitHub Actions test, documentation, and PyPI release workflows.
- Added issue and pull-request templates.

## 0.1.0

Initial public release.

Included timezone-aware scheduling, weekly schedules, date overrides, closures, multiple windows, breaks, DST policies, rolling availability, capacity, booking buffers, booking policies, blocked periods, reservations, cancellation, and in-memory booking storage.
