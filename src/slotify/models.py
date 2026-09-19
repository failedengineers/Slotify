from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Any, Mapping

from .exceptions import InvalidTimeError


def _ensure_time(value: time) -> time:
    if not isinstance(value, time):
        raise InvalidTimeError("Expected a datetime.time instance.")

    if value.tzinfo is not None:
        raise InvalidTimeError(
            "Schedule times must be timezone-naive. "
            "Configure the timezone separately."
        )

    return value


def _ensure_aware(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware.")

    return value


def _as_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class TimeWindow:
    """
    A recurring local-time scheduling window.

    Example:
        TimeWindow.from_strings("09:00", "17:00")

    Overnight windows are supported:

        TimeWindow.from_strings("22:00", "02:00")
    """

    start: time
    end: time

    def __post_init__(self) -> None:
        _ensure_time(self.start)
        _ensure_time(self.end)

        if self.start == self.end:
            raise InvalidTimeError(
                "TimeWindow start and end cannot be equal."
            )

    @classmethod
    def from_strings(cls, start: str, end: str) -> "TimeWindow":
        try:
            start_time = time.fromisoformat(start)
            end_time = time.fromisoformat(end)
        except (TypeError, ValueError) as exc:
            raise InvalidTimeError(
                "Times must use HH:MM, HH:MM:SS, "
                "or ISO time format."
            ) from exc

        return cls(start_time, end_time)

    @property
    def crosses_midnight(self) -> bool:
        return self.end < self.start

    @property
    def duration(self) -> timedelta:
        start_seconds = (
            self.start.hour * 3600
            + self.start.minute * 60
            + self.start.second
            + self.start.microsecond / 1_000_000
        )

        end_seconds = (
            self.end.hour * 3600
            + self.end.minute * 60
            + self.end.second
            + self.end.microsecond / 1_000_000
        )

        if end_seconds < start_seconds:
            end_seconds += 24 * 3600

        return timedelta(seconds=end_seconds - start_seconds)

    def contains(self, value: time) -> bool:
        value = _ensure_time(value)

        if self.crosses_midnight:
            return value >= self.start or value < self.end

        return self.start <= value < self.end


@dataclass(frozen=True, slots=True)
class Slot:
    """
    Immutable timezone-aware appointment slot.

    Duration is calculated using UTC instants, which avoids incorrect
    arithmetic around daylight-saving transitions.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _ensure_aware(self.start, "start")
        _ensure_aware(self.end, "end")

        if _as_utc(self.end) <= _as_utc(self.start):
            raise ValueError("Slot end must be after slot start.")

    @property
    def duration(self) -> timedelta:
        return _as_utc(self.end) - _as_utc(self.start)

    @property
    def start_utc(self) -> datetime:
        return _as_utc(self.start)

    @property
    def end_utc(self) -> datetime:
        return _as_utc(self.end)

    def overlaps(self, other: "Slot") -> bool:
        if not isinstance(other, Slot):
            raise TypeError("other must be a Slot.")

        return (
            self.start_utc < other.end_utc
            and other.start_utc < self.end_utc
        )

    def contains(self, value: datetime) -> bool:
        _ensure_aware(value, "value")

        instant = value.astimezone(timezone.utc)

        return self.start_utc <= instant < self.end_utc

    def in_timezone(self, tz: Any) -> "Slot":
        from .timezone import get_timezone

        zone = get_timezone(tz)

        return Slot(
            self.start.astimezone(zone),
            self.end.astimezone(zone),
        )

    def to_dict(self) -> Mapping[str, Any]:
        timezone_name = getattr(
            self.start.tzinfo,
            "key",
            str(self.start.tzinfo),
        )

        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_seconds": int(
                self.duration.total_seconds()
            ),
            "timezone": timezone_name,
        }