# Timezones & DST

Scheduling should be defined in the timezone of the resource being scheduled.

## Use IANA timezone names

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="America/New_York",
)
~~~

Examples of IANA names include:

~~~text
Asia/Kolkata
America/New_York
Europe/London
Australia/Sydney
UTC
~~~

## Why this matters

A provider working 09:00–17:00 in India should not suddenly become a 09:00–17:00 schedule in the server's timezone just because the application server moved.

Store the resource timezone and pass it to Slotify.

## DST transitions

During daylight-saving transitions, local clock times can be:

- normal
- ambiguous because a clock repeats an interval
- nonexistent because a clock skips an interval

Slotify lets you choose how those cases are handled.

~~~python
generator = SlotGenerator(
    start="01:00",
    end="03:00",
    duration=30,
    timezone="America/New_York",
    dst_ambiguous="raise",
    dst_nonexistent="skip",
)
~~~

Ambiguous-time policies:

~~~text
raise
earlier
later
both
~~~

Nonexistent-time policies:

~~~text
raise
skip
~~~

## Testing DST behavior

Use explicit dates and times in tests:

~~~python
slots = generator.generate_for_date("2026-11-01")
~~~

For rolling availability:

~~~python
from datetime import datetime

slots = generator.upcoming(
    7,
    now=datetime.fromisoformat(
        "2026-09-21T08:00:00-04:00"
    ),
)
~~~

Passing `now` makes tests deterministic.

## Windows

On Windows, Slotify declares `tzdata` as a runtime dependency automatically.

For production systems, test the timezones your application actually supports.
