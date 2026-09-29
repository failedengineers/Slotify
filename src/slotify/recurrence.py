from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterator, Literal


Frequency = Literal["daily", "weekly", "monthly", "yearly"]


@dataclass(frozen=True, slots=True)
class RecurrenceRule:
    """
    Recurrence rule for appointment series.

    frequency may be daily, weekly, monthly, or yearly.
    interval is measured in units of frequency.
    weekdays is used by weekly rules.
    day_of_month is used by monthly rules.
    count and until are mutually exclusive.
    excluded_dates are skipped without consuming a count occurrence.
    """

    frequency: Frequency = "weekly"
    weekdays: tuple[int, ...] = ()
    interval: int = 1
    count: int | None = None
    until: date | datetime | str | None = None
    day_of_month: int | None = None
    excluded_dates: tuple[date | datetime | str, ...] = ()

    def __post_init__(self) -> None:
        if self.frequency not in {"daily", "weekly", "monthly", "yearly"}:
            raise ValueError(
                "frequency must be 'daily', 'weekly', 'monthly', or 'yearly'."
            )

        days = tuple(sorted(set(self.weekdays)))
        if any(
            isinstance(day, bool) or not isinstance(day, int) or not 0 <= day <= 6
            for day in days
        ):
            raise ValueError("weekdays must contain integers from 0 to 6.")
        if self.frequency != "weekly" and days:
            raise ValueError("weekdays can only be used with weekly recurrence.")

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

        until = self._coerce_date(self.until, "until") if self.until is not None else None

        if self.day_of_month is not None and (
            isinstance(self.day_of_month, bool)
            or not isinstance(self.day_of_month, int)
            or not 1 <= self.day_of_month <= 31
        ):
            raise ValueError("day_of_month must be an integer from 1 to 31 or None.")

        exclusions = tuple(
            self._coerce_date(value, "excluded_dates")
            for value in self.excluded_dates
        )

        if self.frequency == "monthly" and self.day_of_month is None:
            object.__setattr__(self, "day_of_month", None)

        object.__setattr__(self, "weekdays", days)
        object.__setattr__(self, "until", until)
        object.__setattr__(self, "excluded_dates", tuple(sorted(set(exclusions))))

    @staticmethod
    def _coerce_date(value, name: str) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{name} contains an invalid ISO date.") from exc
        raise TypeError(
            f"{name} must contain date, datetime, or YYYY-MM-DD values."
        )

    def _should_emit(self, candidate: date) -> bool:
        return candidate not in self.excluded_dates

    def occurrences(self, start: date | datetime | str) -> Iterator[date]:
        first = self._coerce_date(start, "start")
        emitted = 0

        if self.frequency == "daily":
            step = timedelta(days=self.interval)
            candidate = first
            while self.until is None or candidate <= self.until:
                if self._should_emit(candidate):
                    yield candidate
                    emitted += 1
                    if self.count is not None and emitted >= self.count:
                        return
                candidate += step
            return

        if self.frequency == "weekly":
            weekdays = self.weekdays or (first.weekday(),)
            week_start = first - timedelta(days=first.weekday())
            while True:
                for weekday in weekdays:
                    candidate = week_start + timedelta(days=weekday)
                    if candidate < first:
                        continue
                    if self.until is not None and candidate > self.until:
                        return
                    if self._should_emit(candidate):
                        yield candidate
                        emitted += 1
                        if self.count is not None and emitted >= self.count:
                            return
                week_start += timedelta(weeks=self.interval)

        if self.frequency == "monthly":
            day = self.day_of_month or first.day
            year, month = first.year, first.month
            while True:
                actual_day = min(day, monthrange(year, month)[1])
                candidate = date(year, month, actual_day)
                if candidate >= first:
                    if self.until is not None and candidate > self.until:
                        return
                    if self._should_emit(candidate):
                        yield candidate
                        emitted += 1
                        if self.count is not None and emitted >= self.count:
                            return
                month_index = year * 12 + (month - 1) + self.interval
                year, month = divmod(month_index, 12)
                month += 1

        if self.frequency == "yearly":
            month = first.month
            day = self.day_of_month or first.day
            year = first.year
            while True:
                try:
                    candidate = date(year, month, day)
                except ValueError:
                    candidate = date(year, month, monthrange(year, month)[1])
                if candidate >= first:
                    if self.until is not None and candidate > self.until:
                        return
                    if self._should_emit(candidate):
                        yield candidate
                        emitted += 1
                        if self.count is not None and emitted >= self.count:
                            return
                year += self.interval
