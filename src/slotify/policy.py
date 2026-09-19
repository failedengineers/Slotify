from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .exceptions import SlotUnavailableError
from .models import Slot


@dataclass(frozen=True, slots=True)
class BlockedPeriod:
    """
    A timezone-aware interval during which bookings are prohibited.
    """

    start: datetime
    end: datetime
    reason: str = "Unavailable"

    def __post_init__(self) -> None:
        if (
            self.start.tzinfo is None
            or self.start.utcoffset() is None
            or self.end.tzinfo is None
            or self.end.utcoffset() is None
        ):
            raise ValueError(
                "BlockedPeriod datetimes must be timezone-aware."
            )

        if self.end.astimezone(timezone.utc) <= (
            self.start.astimezone(timezone.utc)
        ):
            raise ValueError(
                "BlockedPeriod end must be after start."
            )

    def overlaps(self, slot: Slot) -> bool:
        start = self.start.astimezone(timezone.utc)
        end = self.end.astimezone(timezone.utc)

        return (
            slot.start_utc < end
            and start < slot.end_utc
        )


@dataclass(frozen=True, slots=True)
class BookingPolicy:
    """
    Rules that determine whether a generated slot can be booked.

    minimum_notice:
        Required lead time before the appointment.

    maximum_horizon:
        Furthest allowed appointment start from now.

    blocked_periods:
        Explicit unavailable periods such as holidays,
        maintenance windows or provider leave.
    """

    minimum_notice: timedelta = timedelta(0)

    maximum_horizon: timedelta | None = None

    blocked_periods: tuple[BlockedPeriod, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_notice < timedelta(0):
            raise ValueError(
                "minimum_notice cannot be negative."
            )

        if (
            self.maximum_horizon is not None
            and self.maximum_horizon <= timedelta(0)
        ):
            raise ValueError(
                "maximum_horizon must be greater than zero."
            )

        object.__setattr__(
            self,
            "blocked_periods",
            tuple(self.blocked_periods),
        )

    def validate(
        self,
        slot: Slot,
        *,
        now: datetime,
    ) -> None:
        if (
            now.tzinfo is None
            or now.utcoffset() is None
        ):
            raise ValueError(
                "now must be timezone-aware."
            )

        now_utc = now.astimezone(timezone.utc)

        earliest_allowed = (
            now_utc
            + self.minimum_notice
        )

        if slot.start_utc < earliest_allowed:
            raise SlotUnavailableError(
                "Slot violates the minimum booking notice."
            )

        if self.maximum_horizon is not None:
            latest_allowed = (
                now_utc
                + self.maximum_horizon
            )

            if slot.start_utc > latest_allowed:
                raise SlotUnavailableError(
                    "Slot is outside the booking horizon."
                )

        for blocked in self.blocked_periods:
            if blocked.overlaps(slot):
                raise SlotUnavailableError(
                    blocked.reason
                    or "Slot falls inside a blocked period."
                )

    def is_bookable(
        self,
        slot: Slot,
        *,
        now: datetime,
    ) -> bool:
        try:
            self.validate(
                slot,
                now=now,
            )
        except SlotUnavailableError:
            return False

        return True