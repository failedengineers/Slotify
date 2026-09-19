from __future__ import annotations

from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)
from typing import Iterable, Sequence

from .exceptions import (
    ConfigurationError,
    DSTTransitionError,
    InvalidDateRangeError,
)
from .models import Slot, TimeWindow
from .schedule import Schedule
from .timezone import (
    get_timezone,
    local_datetime_candidates,
    resolve_local_datetime,
)


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


class SlotGenerator:
    """
    Generate timezone-aware appointment slots.

    Supports:

    - fixed or custom intervals
    - multiple daily windows
    - overnight windows
    - weekdays
    - schedule-based weekly rules
    - date-specific schedule overrides
    - excluded dates
    - breaks
    - IANA timezones
    - DST ambiguous-time handling
    - DST nonexistent-time handling
    - deterministic date generation
    - rolling/upcoming slots
    """

    def __init__(
        self,
        *,
        start: str | time | None = None,
        end: str | time | None = None,
        schedule: Schedule | None = None,
        windows: Sequence[
            TimeWindow
            | tuple[str | time, str | time]
        ]
        | None = None,
        duration: int | timedelta = 30,
        interval: int | timedelta | None = None,
        timezone: str = "UTC",
        weekdays: Iterable[int | str] | None = None,
        breaks: Sequence[
            TimeWindow
            | tuple[str | time, str | time]
        ] = (),
        excluded_dates: Iterable[
            date | datetime | str
        ] = (),
        dst_ambiguous: str = "raise",
        dst_nonexistent: str = "raise",
    ) -> None:

        self.timezone = get_timezone(timezone)

        if schedule is not None:
            if (
                start is not None
                or end is not None
                or windows is not None
                or weekdays is not None
            ):
                raise ConfigurationError(
                    "When schedule is provided, do not also "
                    "provide start, end, windows, or weekdays."
                )

            self.schedule = schedule
            self.windows = ()
            self.weekdays = frozenset()

        else:
            self.schedule = None

            if (
                windows is not None
                and (
                    start is not None
                    or end is not None
                )
            ):
                raise ConfigurationError(
                    "Provide either start/end or windows, "
                    "not both."
                )

            if windows is None:
                if start is None or end is None:
                    raise ConfigurationError(
                        "Both start and end are required "
                        "when schedule is not provided."
                    )

                windows = [(start, end)]

            self.windows = tuple(
                self._coerce_window(window)
                for window in windows
            )

            if not self.windows:
                raise ConfigurationError(
                    "At least one scheduling window "
                    "is required."
                )

            self.weekdays = self._coerce_weekdays(
                weekdays
            )

        self.breaks = tuple(
            self._coerce_window(window)
            for window in breaks
        )

        self.duration = self._coerce_duration(
            duration,
            "duration",
        )

        self.interval = (
            self._coerce_duration(
                interval,
                "interval",
            )
            if interval is not None
            else self.duration
        )

        self.excluded_dates = frozenset(
            self._coerce_date(value)
            for value in excluded_dates
        )

        if dst_ambiguous not in {
            "raise",
            "earlier",
            "later",
            "both",
        }:
            raise ConfigurationError(
                "dst_ambiguous must be "
                "'raise', 'earlier', 'later', "
                "or 'both'."
            )

        if dst_nonexistent not in {
            "raise",
            "skip",
        }:
            raise ConfigurationError(
                "dst_nonexistent must be "
                "'raise' or 'skip'."
            )

        self.dst_ambiguous = dst_ambiguous
        self.dst_nonexistent = dst_nonexistent

    @staticmethod
    def _coerce_duration(
        value: int | timedelta,
        name: str,
    ) -> timedelta:

        if isinstance(value, bool):
            raise TypeError(
                f"{name} must be an integer number "
                "of minutes or timedelta."
            )

        if isinstance(value, int):
            result = timedelta(minutes=value)

        elif isinstance(value, timedelta):
            result = value

        else:
            raise TypeError(
                f"{name} must be an integer number "
                "of minutes or timedelta."
            )

        if result <= timedelta(0):
            raise ConfigurationError(
                f"{name} must be greater than zero."
            )

        return result

    @staticmethod
    def _coerce_window(
        value: TimeWindow
        | tuple[str | time, str | time],
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
    def _coerce_weekdays(
        values: Iterable[int | str] | None,
    ) -> frozenset[int]:

        if values is None:
            return frozenset(range(7))

        result: set[int] = set()

        for value in values:
            if isinstance(value, str):
                key = value.strip().lower()

                if key not in _WEEKDAYS:
                    raise ConfigurationError(
                        f"Unknown weekday: {value!r}."
                    )

                result.add(_WEEKDAYS[key])

            elif (
                isinstance(value, int)
                and not isinstance(value, bool)
                and 0 <= value <= 6
            ):
                result.add(value)

            else:
                raise ConfigurationError(
                    "Weekdays must be names or integers "
                    "from 0 (Monday) to 6 (Sunday)."
                )

        return frozenset(result)

    def _windows_for_date(
        self,
        day: date,
    ) -> tuple[TimeWindow, ...]:

        if day in self.excluded_dates:
            return ()

        if self.schedule is not None:
            return self.schedule.windows_for(day)

        if day.weekday() not in self.weekdays:
            return ()

        return self.windows

    def _window_bounds(
        self,
        day: date,
        window: TimeWindow,
    ) -> tuple[datetime, datetime]:

        end_day = (
            day + timedelta(days=1)
            if window.crosses_midnight
            else day
        )

        start = resolve_local_datetime(
            day,
            window.start,
            self.timezone,
            ambiguous=(
                "later"
                if self.dst_ambiguous == "later"
                else "earlier"
            ),
        )

        end = resolve_local_datetime(
            end_day,
            window.end,
            self.timezone,
            ambiguous=(
                "earlier"
                if self.dst_ambiguous == "earlier"
                else "later"
            ),
        )

        if (
            end.astimezone(timezone.utc)
            <= start.astimezone(timezone.utc)
        ):
            raise ConfigurationError(
                "Scheduling window resolves to "
                "an invalid interval."
            )

        return start, end

    def _start_candidates(
        self,
        naive: datetime,
    ) -> tuple[datetime, ...]:

        try:
            candidates = local_datetime_candidates(
                naive,
                None,
                self.timezone,
            )

        except DSTTransitionError:
            if self.dst_nonexistent == "skip":
                return ()

            raise

        if len(candidates) == 1:
            return candidates

        if self.dst_ambiguous == "raise":
            raise DSTTransitionError(
                f"Ambiguous local time "
                f"{naive.isoformat()} in "
                f"{getattr(self.timezone, 'key', self.timezone)!s}."
            )

        ordered = sorted(
            candidates,
            key=lambda value: value.astimezone(
                timezone.utc
            ),
        )

        if self.dst_ambiguous == "earlier":
            return (ordered[0],)

        if self.dst_ambiguous == "later":
            return (ordered[-1],)

        return tuple(ordered)

    def _overlaps_break(
        self,
        start: datetime,
        end: datetime,
    ) -> bool:

        local_day = start.astimezone(
            self.timezone
        ).date()

        for anchor_day in (
            local_day - timedelta(days=1),
            local_day,
        ):
            for window in self.breaks:
                break_start, break_end = (
                    self._window_bounds(
                        anchor_day,
                        window,
                    )
                )

                if (
                    start.astimezone(timezone.utc)
                    < break_end.astimezone(timezone.utc)
                    and break_start.astimezone(timezone.utc)
                    < end.astimezone(timezone.utc)
                ):
                    return True

        return False

    def generate_for_date(
        self,
        day: date | datetime | str,
    ) -> list[Slot]:

        target = self._coerce_date(day)

        windows = self._windows_for_date(target)

        if not windows:
            return []

        unique_slots: dict[
            tuple[datetime, datetime],
            Slot,
        ] = {}

        for window in windows:

            window_start, window_end = (
                self._window_bounds(
                    target,
                    window,
                )
            )

            naive_start = datetime.combine(
                target,
                window.start,
            )

            elapsed = timedelta(0)

            while elapsed < window.duration:

                for slot_start in self._start_candidates(
                    naive_start
                ):
                    slot_start_utc = (
                        slot_start.astimezone(
                            timezone.utc
                        )
                    )

                    window_end_utc = (
                        window_end.astimezone(
                            timezone.utc
                        )
                    )

                    if slot_start_utc >= window_end_utc:
                        continue

                    slot_end_utc = (
                        slot_start_utc
                        + self.duration
                    )

                    if slot_end_utc > window_end_utc:
                        continue

                    slot_end = (
                        slot_end_utc.astimezone(
                            self.timezone
                        )
                    )

                    if self._overlaps_break(
                        slot_start,
                        slot_end,
                    ):
                        continue

                    slot = Slot(
                        slot_start,
                        slot_end,
                    )

                    key = (
                        slot.start_utc,
                        slot.end_utc,
                    )

                    unique_slots[key] = slot

                naive_start += self.interval
                elapsed += self.interval

        return sorted(
            unique_slots.values(),
            key=lambda slot: slot.start_utc,
        )

    def generate(
        self,
        start_date: date | datetime | str,
        end_date: date | datetime | str | None = None,
    ) -> list[Slot]:

        start = self._coerce_date(
            start_date
        )

        end = self._coerce_date(
            end_date
            if end_date is not None
            else start_date
        )

        if end < start:
            raise InvalidDateRangeError(
                "end_date must be greater than "
                "or equal to start_date."
            )

        result: list[Slot] = []

        current = start

        while current <= end:
            result.extend(
                self.generate_for_date(current)
            )
            current += timedelta(days=1)

        return result

    def upcoming(
        self,
        days: int,
        *,
        now: datetime | None = None,
    ) -> list[Slot]:

        if (
            isinstance(days, bool)
            or not isinstance(days, int)
            or days < 1
        ):
            raise ConfigurationError(
                "days must be a positive integer."
            )

        if now is None:
            now = datetime.now(
                self.timezone
            )

        elif (
            now.tzinfo is None
            or now.utcoffset() is None
        ):
            now = now.replace(
                tzinfo=self.timezone
            )

        else:
            now = now.astimezone(
                self.timezone
            )

        slots = self.generate(
            now.date(),
            now.date()
            + timedelta(days=days - 1),
        )

        now_utc = now.astimezone(
            timezone.utc
        )

        return [
            slot
            for slot in slots
            if slot.start_utc >= now_utc
        ]