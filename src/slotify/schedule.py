from __future__ import annotations

from datetime import date, datetime, time
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

from .exceptions import ConfigurationError, InvalidDateRangeError
from .models import TimeWindow


_WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}


WindowInput = (
    TimeWindow
    | tuple[str | time, str | time]
)


class Schedule:
    """
    Weekly scheduling rules with optional date-specific overrides.

    An override replaces the entire weekly schedule for a date.

    An empty override means the date is closed.

    Explicit closed dates and annual closed dates take priority
    over both weekly schedules and date overrides.
    """

    __slots__ = (
        "_weekly",
        "_overrides",
        "_closed_dates",
        "_annual_closed_dates",
    )

    def __init__(
        self,
        *,
        weekly: Mapping[
            int | str,
            Sequence[WindowInput],
        ],
        overrides: Mapping[
            date | datetime | str,
            Sequence[WindowInput] | None,
        ] | None = None,
        closed_dates: Iterable[
            date | datetime | str
        ] = (),
        annual_closed_dates: Iterable[
            str | tuple[int, int]
        ] = (),
    ) -> None:

        if not isinstance(weekly, Mapping):
            raise TypeError(
                "weekly must be a mapping of weekdays to windows."
            )

        normalized_weekly: dict[
            int,
            tuple[TimeWindow, ...],
        ] = {}

        for weekday, windows in weekly.items():
            day_number = self._coerce_weekday(
                weekday
            )

            if day_number in normalized_weekly:
                raise ConfigurationError(
                    f"Duplicate schedule for weekday "
                    f"{weekday!r}."
                )

            normalized_weekly[day_number] = (
                self._coerce_windows(windows)
            )

        normalized_overrides: dict[
            date,
            tuple[TimeWindow, ...],
        ] = {}

        for override_date, windows in (
            (overrides or {}).items()
        ):
            target = self._coerce_date(
                override_date
            )

            if target in normalized_overrides:
                raise ConfigurationError(
                    f"Duplicate override for "
                    f"{target.isoformat()}."
                )

            normalized_overrides[target] = (
                ()
                if windows is None
                else self._coerce_windows(windows)
            )

        normalized_closed_dates = frozenset(
            self._coerce_date(value)
            for value in closed_dates
        )

        normalized_annual_closed_dates = frozenset(
            self._coerce_annual_date(value)
            for value in annual_closed_dates
        )

        self._weekly = MappingProxyType(
            normalized_weekly
        )

        self._overrides = MappingProxyType(
            normalized_overrides
        )

        self._closed_dates = (
            normalized_closed_dates
        )

        self._annual_closed_dates = (
            normalized_annual_closed_dates
        )

    @staticmethod
    def _coerce_weekday(
        value: int | str,
    ) -> int:

        if isinstance(value, str):
            key = value.strip().lower()

            if key not in _WEEKDAYS:
                raise ConfigurationError(
                    f"Unknown weekday: {value!r}."
                )

            return _WEEKDAYS[key]

        if (
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 6
        ):
            return value

        raise ConfigurationError(
            "Weekday must be a name or an integer "
            "from 0 (Monday) to 6 (Sunday)."
        )

    @staticmethod
    def _coerce_date(
        value: date | datetime | str,
    ) -> date:

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise InvalidDateRangeError(
                    f"Invalid date: {value!r}"
                ) from exc

        raise TypeError(
            "Date values must be date, datetime, "
            "or YYYY-MM-DD strings."
        )

    @staticmethod
    def _coerce_annual_date(
        value: str | tuple[int, int],
    ) -> tuple[int, int]:

        if isinstance(value, str):
            try:
                parts = value.strip().split("-")

                if len(parts) != 2:
                    raise ValueError

                month_number = int(parts[0])
                day_number = int(parts[1])

                # 2024 is a leap year so 02-29 is valid.
                date(
                    2024,
                    month_number,
                    day_number,
                )

                return month_number, day_number

            except (TypeError, ValueError) as exc:
                raise ConfigurationError(
                    f"Invalid annual closed date: {value!r}. "
                    "Use 'MM-DD'."
                ) from exc

        if (
            isinstance(value, tuple)
            and len(value) == 2
        ):
            month_number, day_number = value

            if not (
                isinstance(month_number, int)
                and not isinstance(month_number, bool)
                and isinstance(day_number, int)
                and not isinstance(day_number, bool)
            ):
                raise ConfigurationError(
                    "Annual closed dates must contain "
                    "integer month and day values."
                )

            try:
                date(
                    2024,
                    month_number,
                    day_number,
                )
            except ValueError as exc:
                raise ConfigurationError(
                    f"Invalid annual closed date: {value!r}."
                ) from exc

            return month_number, day_number

        raise ConfigurationError(
            "Annual closed dates must use "
            "'MM-DD' or (month, day)."
        )

    @staticmethod
    def _coerce_window(
        value: WindowInput,
    ) -> TimeWindow:

        if isinstance(value, TimeWindow):
            return value

        if (
            isinstance(value, (tuple, list))
            and len(value) == 2
        ):
            start, end = value

            if (
                isinstance(start, str)
                and isinstance(end, str)
            ):
                return TimeWindow.from_strings(
                    start,
                    end,
                )

            if (
                isinstance(start, time)
                and isinstance(end, time)
            ):
                return TimeWindow(
                    start,
                    end,
                )

        raise TypeError(
            "Each window must be a TimeWindow "
            "or a (start, end) pair."
        )

    @classmethod
    def _coerce_windows(
        cls,
        windows: Sequence[WindowInput],
    ) -> tuple[TimeWindow, ...]:

        if isinstance(windows, (str, bytes)):
            raise TypeError(
                "Windows must be a sequence of "
                "TimeWindow objects or (start, end) pairs."
            )

        return tuple(
            cls._coerce_window(window)
            for window in windows
        )

    @property
    def weekly(
        self,
    ) -> Mapping[
        int,
        tuple[TimeWindow, ...],
    ]:
        return self._weekly

    @property
    def overrides(
        self,
    ) -> Mapping[
        date,
        tuple[TimeWindow, ...],
    ]:
        return self._overrides

    @property
    def closed_dates(
        self,
    ) -> frozenset[date]:
        return self._closed_dates

    @property
    def annual_closed_dates(
        self,
    ) -> frozenset[tuple[int, int]]:
        return self._annual_closed_dates

    def windows_for(
        self,
        day: date | datetime | str,
    ) -> tuple[TimeWindow, ...]:

        target = self._coerce_date(day)

        # Explicit closures have highest priority.
        if target in self._closed_dates:
            return ()

        # Recurring annual closures come next.
        if (
            target.month,
            target.day,
        ) in self._annual_closed_dates:
            return ()

        # A date override replaces the weekly schedule.
        if target in self._overrides:
            return self._overrides[target]

        # Fall back to the normal weekly schedule.
        return self._weekly.get(
            target.weekday(),
            (),
        )

    def is_open(
        self,
        day: date | datetime | str,
    ) -> bool:
        return bool(
            self.windows_for(day)
        )