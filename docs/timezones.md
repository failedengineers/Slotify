# Timezones & DST

Slotify accepts IANA timezone names.

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="America/New_York",
)
~~~

## Why the timezone matters

A schedule defined as 09:00–17:00 is local to the resource's timezone. Two resources in different regions can therefore use the same scheduling model with different timezone values.

## DST behavior

During a daylight-saving transition, a local clock time can be ambiguous or nonexistent.

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

Ambiguous policies:

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

## Deterministic tests

~~~python
from datetime import datetime

slots = generator.upcoming(
    7,
    now=datetime.fromisoformat("2026-09-21T08:00:00-04:00"),
)
~~~

For production systems, store the resource timezone explicitly and test DST transitions for every supported region.
