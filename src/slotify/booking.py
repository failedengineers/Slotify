from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from types import MappingProxyType
from typing import Any, Iterable, Literal, Mapping, Protocol
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
    A booking may reserve one or more resources. When resource_ids is
    provided, any overlapping booking sharing at least one resource
    conflicts with it.
    """

    slot: Slot
    resource_id: str | None = None
    booking_id: str = field(default_factory=lambda: str(uuid4()))
    status: BookingStatus = "confirmed"
    buffer_before: timedelta = timedelta(0)
    buffer_after: timedelta = timedelta(0)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)
    resource_ids: tuple[str, ...] = ()
    series_id: str | None = None
    rescheduled_count: int = 0

    def __post_init__(self) -> None:
        if not self.booking_id:
            raise ValueError("booking_id cannot be empty.")

        if self.status not in {"confirmed", "cancelled"}:
            raise ValueError(
                "status must be 'confirmed' or 'cancelled'."
            )

        if self.buffer_before < timedelta(0):
            raise ValueError("buffer_before cannot be negative.")

        if self.buffer_after < timedelta(0):
            raise ValueError("buffer_after cannot be negative.")

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError("created_at must be timezone-aware.")

        if (
            isinstance(self.rescheduled_count, bool)
            or not isinstance(self.rescheduled_count, int)
            or self.rescheduled_count < 0
        ):
            raise ValueError(
                "rescheduled_count must be a non-negative integer."
            )

        normalized_resources: list[str] = []

        for value in self.resource_ids:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    "resource_ids must contain non-empty strings."
                )
            if value not in normalized_resources:
                normalized_resources.append(value)

        if self.resource_id is not None:
            if (
                not isinstance(self.resource_id, str)
                or not self.resource_id.strip()
            ):
                raise ValueError(
                    "resource_id must be a non-empty string or None."
                )
            if self.resource_id not in normalized_resources:
                normalized_resources.insert(0, self.resource_id)

        object.__setattr__(
            self,
            "resource_ids",
            tuple(normalized_resources),
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def effective_resource_ids(self) -> tuple[str | None, ...]:
        if self.resource_ids:
            return self.resource_ids
        return (self.resource_id,)

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
        if not isinstance(other, Booking):
            raise TypeError("other must be a Booking.")

        if not set(self.effective_resource_ids).intersection(
            other.effective_resource_ids
        ):
            return False

        return (
            self.protected_start < other.protected_end
            and other.protected_start < self.protected_end
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
            resource_ids=self.resource_ids,
            series_id=self.series_id,
            rescheduled_count=self.rescheduled_count,
        )

    def reschedule(self, new_slot: Slot) -> "Booking":
        if self.status != "confirmed":
            raise ValueError("Only confirmed bookings can be rescheduled.")

        return Booking(
            slot=new_slot,
            resource_id=self.resource_id,
            booking_id=self.booking_id,
            status="confirmed",
            buffer_before=self.buffer_before,
            buffer_after=self.buffer_after,
            created_at=self.created_at,
            metadata=self.metadata,
            resource_ids=self.resource_ids,
            series_id=self.series_id,
            rescheduled_count=self.rescheduled_count + 1,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "booking_id": self.booking_id,
            "resource_id": self.resource_id,
            "resource_ids": list(self.resource_ids),
            "status": self.status,
            "series_id": self.series_id,
            "rescheduled_count": self.rescheduled_count,
            "slot": self.slot.to_dict(),
            "protected_start": self.protected_start.isoformat(),
            "protected_end": self.protected_end.isoformat(),
            "created_at": self.created_at.isoformat(),
            "metadata": dict(self.metadata),
        }

    def to_ics(
        self,
        *,
        summary: str = "Appointment",
        description: str | None = None,
        location: str | None = None,
    ) -> str:
        from .ics import booking_to_ics

        return booking_to_ics(
            self,
            summary=summary,
            description=description,
            location=location,
        )


class BookingStore(Protocol):
    """
    Storage interface.

    Implementations must make reserve() and reschedule() atomic for
    their underlying storage system.
    """

    def reserve(self, booking: Booking) -> Booking:
        ...

    def cancel(self, booking_id: str) -> Booking:
        ...

    def reschedule(
        self,
        booking_id: str,
        new_slot: Slot,
    ) -> Booking:
        ...

    def get(self, booking_id: str) -> Booking:
        ...

    def list(
        self,
        *,
        resource_id: str | None = None,
        series_id: str | None = None,
        include_cancelled: bool = False,
    ) -> list[Booking]:
        ...

    def available_capacity(
        self,
        booking: Booking,
        *,
        capacity: int,
        exclude_booking_id: str | None = None,
    ) -> int:
        ...


class InMemoryBookingStore:
    """
    Thread-safe in-memory booking store.

    Useful for local applications, tests and single-process services.

    IMPORTANT:
    Thread locking does not provide multi-process or distributed
    database guarantees. Use a durable transactional store for that.
    """

    def __init__(self, *, capacity: int = 1) -> None:
        self._validate_capacity(capacity)
        self.capacity = capacity
        self._lock = RLock()
        self._bookings: dict[str, Booking] = {}

    @staticmethod
    def _validate_capacity(capacity: int) -> None:
        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
        ):
            raise ValueError("capacity must be a positive integer.")

    def _active_bookings(self) -> list[Booking]:
        return [
            booking
            for booking in self._bookings.values()
            if booking.status == "confirmed"
        ]

    @staticmethod
    def _shares_resource(
        first: Booking,
        second: Booking,
    ) -> bool:
        return bool(
            set(first.effective_resource_ids).intersection(
                second.effective_resource_ids
            )
        )

    def _available_capacity_locked(
        self,
        booking: Booking,
        *,
        capacity: int,
        exclude_booking_id: str | None = None,
    ) -> int:
        self._validate_capacity(capacity)

        overlapping = sum(
            1
            for existing in self._active_bookings()
            if (
                existing.booking_id != exclude_booking_id
                and self._shares_resource(existing, booking)
                and existing.protected_start < booking.protected_end
                and booking.protected_start < existing.protected_end
            )
        )

        return max(capacity - overlapping, 0)

    def available_capacity(
        self,
        booking: Booking,
        *,
        capacity: int | None = None,
        exclude_booking_id: str | None = None,
    ) -> int:
        effective_capacity = (
            self.capacity
            if capacity is None
            else capacity
        )

        with self._lock:
            return self._available_capacity_locked(
                booking,
                capacity=effective_capacity,
                exclude_booking_id=exclude_booking_id,
            )

    def reserve(self, booking: Booking) -> Booking:
        with self._lock:
            if booking.booking_id in self._bookings:
                raise BookingConflictError(
                    f"Booking {booking.booking_id!r} already exists."
                )

            if booking.status != "confirmed":
                raise ValueError(
                    "Only confirmed bookings can be reserved."
                )

            available = self._available_capacity_locked(
                booking,
                capacity=self.capacity,
            )

            if available <= 0:
                raise BookingConflictError(
                    "The requested interval is no longer available."
                )

            self._bookings[booking.booking_id] = booking
            return booking

    def cancel(self, booking_id: str) -> Booking:
        with self._lock:
            booking = self._bookings.get(booking_id)

            if booking is None:
                raise BookingNotFoundError(
                    f"Booking {booking_id!r} was not found."
                )

            cancelled = booking.cancel()
            self._bookings[booking_id] = cancelled
            return cancelled

    def reschedule(
        self,
        booking_id: str,
        new_slot: Slot,
    ) -> Booking:
        with self._lock:
            booking = self._bookings.get(booking_id)

            if booking is None:
                raise BookingNotFoundError(
                    f"Booking {booking_id!r} was not found."
                )

            candidate = booking.reschedule(new_slot)

            available = self._available_capacity_locked(
                candidate,
                capacity=self.capacity,
                exclude_booking_id=booking_id,
            )

            if available <= 0:
                raise BookingConflictError(
                    "The requested interval is no longer available."
                )

            self._bookings[booking_id] = candidate
            return candidate

    def get(self, booking_id: str) -> Booking:
        with self._lock:
            booking = self._bookings.get(booking_id)

            if booking is None:
                raise BookingNotFoundError(
                    f"Booking {booking_id!r} was not found."
                )

            return booking

    def list(
        self,
        *,
        resource_id: str | None = None,
        series_id: str | None = None,
        include_cancelled: bool = False,
    ) -> list[Booking]:
        with self._lock:
            result = [
                booking
                for booking in self._bookings.values()
                if (
                    resource_id is None
                    or resource_id in booking.effective_resource_ids
                )
                and (
                    series_id is None
                    or booking.series_id == series_id
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
