# Runnable Examples

The repository contains small scripts you can copy and run:

- basic slot generation — [examples/basic_schedule.py](https://github.com/failedengineers/Slotify/blob/main/examples/basic_schedule.py)
- booking lifecycle — [examples/booking.py](https://github.com/failedengineers/Slotify/blob/main/examples/booking.py)
- temporary holds — [examples/holds.py](https://github.com/failedengineers/Slotify/blob/main/examples/holds.py)
- resource pools — [examples/resource_pool.py](https://github.com/failedengineers/Slotify/blob/main/examples/resource_pool.py)

Run one locally:

~~~bash
python examples/booking.py
~~~

These examples are also executed by the test suite so documentation code is less likely to drift from the actual API.

The Django example is intentionally a service-layer example rather than a complete Django project; it shows where Slotify belongs inside an existing application.
