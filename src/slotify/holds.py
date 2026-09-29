from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any, Mapping, Protocol
from uuid import uuid4

from .booking import Booking
from .exceptions import BookingConflictError, HoldExpiredError, HoldNotFoundError
from .models import Slot


@dataclass(frozen=True, slots=True)
class BookingHold:
    """A temporary reservation that prevents a slot from being booked."""

    slot: Slot
    expires_at: datetime
    resource_id: str | None = None
    hold_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.hold_id:
            raise ValueError("hold_id cannot be empty.")
        if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
            raise ValueError("expires_at must be timezone-aware.")
        if self.resource_id is not None and (
            not isinstance(self.resource_id, str) or not self.resource_id.strip()
        ):
            raise ValueError("resource_id must be a non-empty string or None.")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def resource_ids(self) -> tuple[str | None, ...]:
        return (self.resource_id,)

    def is_active(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("now must be timezone-aware.")
        return current < self.expires_at


class HoldStore(Protocol):
    """Storage interface for temporary booking holds."""

    def create(self, hold: BookingHold) -> BookingHold:
        ...

    def get(self, hold_id: str) -> BookingHold:
        ...

    def release(self, hold_id: str) -> BookingHold:
        ...

    def list(self, *, resource_id: str | None = None) -> list[BookingHold]:
        ...

    def conflicts(
        self,
        booking: Booking,
        *,
        now: datetime | None = None,
        exclude_hold_id: str | None = None,
    ) -> bool:
        ...


class InMemoryHoldStore:
    """Thread-safe in-memory hold store for tests and single-process apps."""

    def __init__(self) -> None:
        self._holds: dict[str, BookingHold] = {}
        self._released: set[str] = set()
        self._lock = RLock()

    @staticmethod
    def _overlaps(hold: BookingHold, booking: Booking) -> bool:
        hold_resources = set(hold.resource_ids)
        booking_resources = set(booking.effective_resource_ids)
        if not hold_resources.intersection(booking_resources):
            return False
        return (
            hold.slot.start_utc < booking.protected_end.astimezone(timezone.utc)
            and booking.protected_start.astimezone(timezone.utc) < hold.slot.end_utc
        )

    def create(self, hold: BookingHold) -> BookingHold:
        with self._lock:
            if hold.hold_id in self._holds:
                raise BookingConflictError(
                    f"Hold {hold.hold_id!r} already exists."
                )
            self._holds[hold.hold_id] = hold
            return hold

    def get(self, hold_id: str) -> BookingHold:
        with self._lock:
            hold = self._holds.get(hold_id)
            if hold is None or hold_id in self._released:
                raise HoldNotFoundError(f"Hold {hold_id!r} was not found.")
            if not hold.is_active():
                raise HoldExpiredError(f"Hold {hold_id!r} has expired.")
            return hold

    def release(self, hold_id: str) -> BookingHold:
        with self._lock:
            hold = self._holds.get(hold_id)
            if hold is None or hold_id in self._released:
                raise HoldNotFoundError(f"Hold {hold_id!r} was not found.")
            self._released.add(hold_id)
            return hold

    def list(self, *, resource_id: str | None = None) -> list[BookingHold]:
        now = datetime.now(timezone.utc)
        with self._lock:
            return sorted(
                [
                    hold for hold in self._holds.values()
                    if hold.hold_id not in self._released
                    and hold.is_active(now)
                    and (
                        resource_id is None
                        or resource_id in hold.resource_ids
                    )
                ],
                key=lambda hold: hold.slot.start_utc,
            )

    def conflicts(
        self,
        booking: Booking,
        *,
        now: datetime | None = None,
        exclude_hold_id: str | None = None,
    ) -> bool:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("now must be timezone-aware.")
        with self._lock:
            return any(
                hold.hold_id != exclude_hold_id
                and hold.hold_id not in self._released
                and hold.is_active(current)
                and self._overlaps(hold, booking)
                for hold in self._holds.values()
            )
