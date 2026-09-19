from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from threading import RLock
from types import MappingProxyType
from typing import Any, Literal, Mapping, Protocol
from uuid import uuid4

from .exceptions import (
    BookingConflictError,
    BookingNotFoundError,
)
from .models import Slot


BookingStatus = Literal["confirmed", "cancelled"]


@dataclass(frozen=True, slots=True)
class Booking:
    """
    Immutable reservation record.

    The protected interval includes optional setup/cleanup buffers.
    """

    slot: Slot
    resource_id: str | None = None
    booking_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    status: BookingStatus = "confirmed"
    buffer_before: timedelta = timedelta(0)
    buffer_after: timedelta = timedelta(0)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.booking_id:
            raise ValueError("booking_id cannot be empty.")

        if self.status not in {
            "confirmed",
            "cancelled",
        }:
            raise ValueError(
                "status must be 'confirmed' or 'cancelled'."
            )

        if self.buffer_before < timedelta(0):
            raise ValueError(
                "buffer_before cannot be negative."
            )

        if self.buffer_after < timedelta(0):
            raise ValueError(
                "buffer_after cannot be negative."
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware."
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def protected_start(self) -> datetime:
        return (
            self.slot.start_utc - self.buffer_before
        ).astimezone(self.slot.start.tzinfo)

    @property
    def protected_end(self) -> datetime:
        return (
            self.slot.end_utc + self.buffer_after
        ).astimezone(self.slot.end.tzinfo)

    def overlaps(self, other: "Booking") -> bool:
        if self.resource_id != other.resource_id:
            return False

        return (
            self.protected_start
            < other.protected_end
            and other.protected_start
            < self.protected_end
        )

    def cancel(self) -> "Booking":
        return Booking(
            slot=self.slot,
            resource_id=self.resource_id,
            booking_id=self.booking_id,
            status="cancelled",
            buffer_before=self.buffer_before,
            buffer_after=self.buffer_after,
            created_at=self.created_at,
            metadata=self.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "booking_id": self.booking_id,
            "resource_id": self.resource_id,
            "status": self.status,
            "slot": self.slot.to_dict(),
            "protected_start": self.protected_start.isoformat(),
            "protected_end": self.protected_end.isoformat(),
            "created_at": self.created_at.isoformat(),
            "metadata": dict(self.metadata),
        }


class BookingStore(Protocol):
    """
    Storage interface.

    Implementations must make reserve() atomic for their
    underlying storage system.
    """

    def reserve(self, booking: Booking) -> Booking:
        ...

    def cancel(self, booking_id: str) -> Booking:
        ...

    def get(self, booking_id: str) -> Booking:
        ...

    def list(
        self,
        *,
        resource_id: str | None = None,
        include_cancelled: bool = False,
    ) -> list[Booking]:
        ...

    def available_capacity(
        self,
        booking: Booking,
        *,
        capacity: int,
    ) -> int:
        ...


class InMemoryBookingStore:
    """
    Thread-safe in-memory booking store.

    Useful for local applications, tests and single-process services.

    IMPORTANT:
    Thread locking does not provide multi-process or distributed
    database guarantees. Database-backed applications should implement
    BookingStore using their database's transaction/locking/unique
    constraint facilities.
    """

    def __init__(self, *, capacity: int = 1) -> None:
        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
        ):
            raise ValueError(
                "capacity must be a positive integer."
            )

        self.capacity = capacity
        self._lock = RLock()
        self._bookings: dict[str, Booking] = {}

    def _active_bookings(
        self,
        *,
        resource_id: str | None,
    ) -> list[Booking]:

        return [
            booking
            for booking in self._bookings.values()
            if (
                booking.status == "confirmed"
                and booking.resource_id == resource_id
            )
        ]

    def available_capacity(
        self,
        booking: Booking,
        *,
        capacity: int | None = None,
    ) -> int:

        effective_capacity = (
            self.capacity
            if capacity is None
            else capacity
        )

        if (
            isinstance(effective_capacity, bool)
            or not isinstance(effective_capacity, int)
            or effective_capacity < 1
        ):
            raise ValueError(
                "capacity must be a positive integer."
            )

        with self._lock:
            overlapping = sum(
                1
                for existing in self._active_bookings(
                    resource_id=booking.resource_id
                )
                if (
                    existing.protected_start
                    < booking.protected_end
                    and booking.protected_start
                    < existing.protected_end
                )
            )

            return max(
                effective_capacity - overlapping,
                0,
            )

    def reserve(self, booking: Booking) -> Booking:
        with self._lock:
            if booking.booking_id in self._bookings:
                raise BookingConflictError(
                    f"Booking {booking.booking_id!r} "
                    "already exists."
                )

            if booking.status != "confirmed":
                raise ValueError(
                    "Only confirmed bookings can be reserved."
                )

            available = self.available_capacity(
                booking,
                capacity=self.capacity,
            )

            if available <= 0:
                raise BookingConflictError(
                    "The requested interval is no longer available."
                )

            self._bookings[
                booking.booking_id
            ] = booking

            return booking

    def cancel(self, booking_id: str) -> Booking:
        with self._lock:
            booking = self._bookings.get(
                booking_id
            )

            if booking is None:
                raise BookingNotFoundError(
                    f"Booking {booking_id!r} was not found."
                )

            cancelled = booking.cancel()

            self._bookings[
                booking_id
            ] = cancelled

            return cancelled

    def get(self, booking_id: str) -> Booking:
        with self._lock:
            booking = self._bookings.get(
                booking_id
            )

            if booking is None:
                raise BookingNotFoundError(
                    f"Booking {booking_id!r} was not found."
                )

            return booking

    def list(
        self,
        *,
        resource_id: str | None = None,
        include_cancelled: bool = False,
    ) -> list[Booking]:

        with self._lock:
            result = [
                booking
                for booking in self._bookings.values()
                if (
                    resource_id is None
                    or booking.resource_id == resource_id
                )
                and (
                    include_cancelled
                    or booking.status == "confirmed"
                )
            ]

            return sorted(
                result,
                key=lambda booking: booking.protected_start,
            )