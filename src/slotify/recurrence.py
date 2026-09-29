from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterator


@dataclass(frozen=True, slots=True)
class RecurrenceRule:
    """
    Weekly recurrence rule for appointment series.

    weekdays uses Python weekday numbers: Monday=0 ... Sunday=6.
    interval is measured in weeks.
    count and until are mutually exclusive.
    """

    weekdays: tuple[int, ...] = ()
    interval: int = 1
    count: int | None = None
    until: date | datetime | str | None = None

    def __post_init__(self) -> None:
        days = tuple(sorted(set(self.weekdays)))

        if any(
            isinstance(day, bool) or not isinstance(day, int) or not 0 <= day <= 6
            for day in days
        ):
            raise ValueError("weekdays must contain integers from 0 to 6.")

        if (
            isinstance(self.interval, bool)
            or not isinstance(self.interval, int)
            or self.interval < 1
        ):
            raise ValueError("interval must be a positive integer.")

        if self.count is not None and (
            isinstance(self.count, bool)
            or not isinstance(self.count, int)
            or self.count < 1
        ):
            raise ValueError("count must be a positive integer or None.")

        if self.count is not None and self.until is not None:
            raise ValueError("count and until cannot both be provided.")

        if self.until is not None:
            value = self.until
            if isinstance(value, datetime):
                value = value.date()
            elif isinstance(value, str):
                value = date.fromisoformat(value)
            elif not isinstance(value, date):
                raise TypeError("until must be a date, datetime, ISO date string, or None.")
            object.__setattr__(self, "until", value)

        object.__setattr__(self, "weekdays", days)

    def occurrences(
        self,
        start: date | datetime | str,
    ) -> Iterator[date]:
        if isinstance(start, datetime):
            first = start.date()
        elif isinstance(start, date):
            first = start
        elif isinstance(start, str):
            first = date.fromisoformat(start)
        else:
            raise TypeError("start must be a date, datetime, or YYYY-MM-DD string.")

        weekdays = self.weekdays or (first.weekday(),)
        emitted = 0
        week_start = first - timedelta(days=first.weekday())

        while True:
            for weekday in weekdays:
                candidate = week_start + timedelta(days=weekday)

                if candidate < first:
                    continue

                if self.until is not None and candidate > self.until:
                    return

                yield candidate
                emitted += 1

                if self.count is not None and emitted >= self.count:
                    return

            week_start += timedelta(weeks=self.interval)
