from __future__ import annotations

from datetime import timedelta
from datetime import datetime
from .policy import BookingPolicy
from .exceptions import SlotUnavailableError

from .booking import (
    Booking,
    BookingStore,
    InMemoryBookingStore,
)
from .exceptions import BookingConflictError
from .generator import SlotGenerator
from .models import Slot


class AvailabilityEngine:
    """
    Converts generated slots into bookable availability.

    Handles:

    - existing bookings
    - per-resource capacity
    - setup buffers
    - cleanup buffers
    - atomic reservation through BookingStore
    """

    def __init__(
    self,
    generator: SlotGenerator,
    *,
    store: BookingStore | None = None,
    resource_id: str | None = None,
    capacity: int = 1,
    buffer_before: int | timedelta = 0,
    buffer_after: int | timedelta = 0,
    policy: BookingPolicy | None = None,
) -> None:
        self.policy = (
        policy
        if policy is not None
        else BookingPolicy()
)

        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
        ):
            raise ValueError(
                "capacity must be a positive integer."
            )

        self.generator = generator
        self.store = (
            store
            if store is not None
            else InMemoryBookingStore(
                capacity=capacity
            )
        )
        self.resource_id = resource_id
        self.capacity = capacity

        self.buffer_before = self._duration(
            buffer_before,
            "buffer_before",
        )

        self.buffer_after = self._duration(
            buffer_after,
            "buffer_after",
        )

    @staticmethod
    def _duration(
        value: int | timedelta,
        name: str,
    ) -> timedelta:

        if isinstance(value, bool):
            raise TypeError(
                f"{name} must be an integer number "
                "of minutes or timedelta."
            )

        if isinstance(value, int):
            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

            return timedelta(minutes=value)

        if isinstance(value, timedelta):
            if value < timedelta(0):
                raise ValueError(
                    f"{name} cannot be negative."
                )

            return value

        raise TypeError(
            f"{name} must be an integer number "
            "of minutes or timedelta."
        )

    def _booking_for(self, slot: Slot) -> Booking:
        return Booking(
            slot=slot,
            resource_id=self.resource_id,
            buffer_before=self.buffer_before,
            buffer_after=self.buffer_after,
        )
    def is_available(
        self,
        slot: Slot,
        *,
        now: datetime | None = None,
    ) -> bool:
        current = (
            now.astimezone(self.generator.timezone)
            if now is not None
            else datetime.now(self.generator.timezone)
        )

        if not self.policy.is_bookable(
            slot,
            now=current,
        ):
            return False

        candidate = self._booking_for(slot)

        return (
            self.store.available_capacity(
                candidate,
                capacity=self.capacity,
            )
            > 0
        )
    def available_slots(
        self,
        start_date,
        end_date=None,
        *,
        now: datetime | None = None,
    ) -> list[Slot]:

        current = (
            now.astimezone(self.generator.timezone)
            if now is not None
            else datetime.now(self.generator.timezone)
        )

        generated = self.generator.generate(
            start_date,
            end_date,
        )

        return [
            slot
            for slot in generated
            if self.is_available(
                slot,
                now=current,
            )
        ]
    def reserve(
        self,
        slot: Slot,
        *,
        metadata=None,
        now: datetime | None = None,
    ) -> Booking:

        current = (
            now.astimezone(self.generator.timezone)
            if now is not None
            else datetime.now(self.generator.timezone)
        )

        self.policy.validate(
            slot,
            now=current,
        )

        booking = Booking(
            slot=slot,
            resource_id=self.resource_id,
            buffer_before=self.buffer_before,
            buffer_after=self.buffer_after,
            metadata=metadata or {},
        )

        return self.store.reserve(booking)

    def reserve_first_available(
        self,
        start_date,
        end_date=None,
        *,
        metadata=None,
    ) -> Booking:

        slots = self.generator.generate(
            start_date,
            end_date,
        )

        for slot in slots:
            try:
                return self.reserve(
                    slot,
                    metadata=metadata,
                )
            except BookingConflictError:
                # Another process/thread may have taken the slot
                # after availability was checked.
                continue

        raise BookingConflictError(
            "No available slot could be reserved."
        )

    def cancel(
        self,
        booking_id: str,
    ) -> Booking:

        return self.store.cancel(
            booking_id
        )