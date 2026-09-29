# Configuration Guide

This page covers the main SlotGenerator and Schedule configuration patterns.

## Fixed working hours

The simplest configuration uses start and end.

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)
~~~

The times are local wall-clock times in the configured timezone.

## Multiple windows

Use windows when the day is split into separate working periods.

~~~python
generator = SlotGenerator(
    windows=[
        ("09:00", "13:00"),
        ("14:00", "18:00"),
    ],
    duration=30,
    timezone="Asia/Kolkata",
)
~~~

Do not pass windows together with start or end.

## Weekdays

With direct start/end or windows, all weekdays are enabled by default.

Restrict the schedule explicitly:

~~~python
generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    weekdays=["monday", "tuesday", "wednesday", "thursday", "friday"],
    timezone="Asia/Kolkata",
)
~~~

Short names work too:

~~~python
weekdays=["mon", "wed", "fri"]
~~~

Python weekday numbering is:

~~~text
Monday=0
Tuesday=1
Wednesday=2
Thursday=3
Friday=4
Saturday=5
Sunday=6
~~~

## Duration and interval

duration controls appointment length.

interval controls the distance between slot start times.

~~~python
generator = SlotGenerator(
    start="09:00",
    end="11:00",
    duration=30,
    interval=15,
    timezone="Asia/Kolkata",
)
~~~

This can generate starts such as:

~~~text
09:00
09:15
09:30
09:45
10:00
...
~~~

Each appointment is still 30 minutes long.

Both duration and interval accept an integer number of minutes or a timedelta.

## Breaks

Breaks remove slots whose intervals overlap the break.

~~~python
generator = SlotGenerator(
    start="09:00",
    end="18:00",
    duration=30,
    breaks=[("13:00", "14:00")],
    timezone="Asia/Kolkata",
)
~~~

## Overnight windows

A window can cross midnight.

~~~python
generator = SlotGenerator(
    windows=[("22:00", "02:00")],
    duration=60,
    timezone="Asia/Kolkata",
)
~~~

The end is interpreted on the following local date.

## Weekly Schedule

Use Schedule when working hours differ by weekday.

~~~python
from slotify import Schedule, SlotGenerator

schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "tuesday": [("10:00", "18:00")],
        "wednesday": [],
        "thursday": [("09:00", "17:00")],
        "friday": [("09:00", "14:00")],
    }
)

generator = SlotGenerator(
    schedule=schedule,
    duration=30,
    timezone="Asia/Kolkata",
)
~~~

An empty list closes that weekday.

## Date-specific overrides

An override replaces the full weekly schedule for one date.

~~~python
schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "tuesday": [("09:00", "17:00")],
    },
    overrides={
        "2026-10-05": [("12:00", "18:00")],
        "2026-10-06": [],
    },
)
~~~

October 5 uses 12:00-18:00 instead of the normal Monday schedule.

October 6 is closed.

## One-off closed dates

Use closed_dates for dates that should always be closed.

~~~python
schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "tuesday": [("09:00", "17:00")],
    },
    closed_dates=["2026-10-02"],
)
~~~

Closed dates have priority over weekly availability and overrides.

## Annual closed dates

Use annual_closed_dates for recurring month/day closures.

~~~python
schedule = Schedule(
    weekly={
        "monday": [("09:00", "17:00")],
        "tuesday": [("09:00", "17:00")],
    },
    annual_closed_dates=["12-25", "01-01"],
)
~~~

Month/day tuples are also supported:

~~~python
annual_closed_dates=[(12, 25), (1, 1)]
~~~

## Excluded dates on SlotGenerator

You can also exclude dates directly from SlotGenerator.

~~~python
generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    excluded_dates=["2026-10-02"],
    timezone="Asia/Kolkata",
)
~~~

## Choosing a scheduling source

Use one of these approaches:

~~~text
start + end
OR
windows
OR
schedule
~~~

When schedule is provided, do not also provide start, end, windows, or weekdays.

## Configuration checklist

For a typical appointment service, define:

~~~text
1. resource timezone
2. working windows
3. appointment duration
4. slot interval
5. breaks
6. holidays / closures
7. booking capacity
8. buffers
9. booking policy
10. durable booking store
~~~
