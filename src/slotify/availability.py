from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4
from .booking import Booking, BookingStore, InMemoryBookingStore
from .exceptions import BookingConflictError, SlotUnavailableError
from .generator import SlotGenerator
from .models import Slot
from .policy import BookingPolicy
from .recurrence import RecurrenceRule


class AvailabilityEngine:
    """
    Converts generated slots into bookable availability.

    Handles bookings, capacity, buffers, resources, booking policies,
    cancellation and rescheduling.
    """

    def __init__(
        self,
        generator: SlotGenerator,
        *,
        store: BookingStore | None = None,
        resource_id: str | None = None,
        resource_ids: tuple[str, ...] | list[str] | None = None,
        capacity: int = 1,
        buffer_before: int | timedelta = 0,
        buffer_after: int | timedelta = 0,
        policy: BookingPolicy | None = None,
    ) -> None:
        self.policy = policy if policy is not None else BookingPolicy()

        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
        ):
            raise ValueError("capacity must be a positive integer.")

        resources = tuple(resource_ids or ())
        if resource_id is not None and resource_id not in resources:
            resources = (resource_id, *resources)

        if not resources:
            resources = (resource_id,) if resource_id is not None else ()

        self.generator = generator
        self.store = (
            store
            if store is not None
            else InMemoryBookingStore(capacity=capacity)
        )
        self.resource_id = resource_id
        self.resource_ids = resources
        self.capacity = capacity
        self.buffer_before = self._duration(buffer_before, "buffer_before")
        self.buffer_after = self._duration(buffer_after, "buffer_after")

    @staticmethod
    def _duration(value: int | timedelta, name: str) -> timedelta:
        if isinstance(value, bool):
            raise TypeError(
                f"{name} must be an integer number of minutes or timedelta."
            )
        if isinstance(value, int):
            if value < 0:
                raise ValueError(f"{name} cannot be negative.")
            return timedelta(minutes=value)
        if isinstance(value, timedelta):
            if value < timedelta(0):
                raise ValueError(f"{name} cannot be negative.")
            return value
        raise TypeError(
            f"{name} must be an integer number of minutes or timedelta."
        )

    def _booking_for(self, slot: Slot, *, metadata=None) -> Booking:
        return Booking(
            slot=slot,
            resource_id=self.resource_id,
            resource_ids=self.resource_ids,
            buffer_before=self.buffer_before,
            buffer_after=self.buffer_after,
            metadata=metadata or {},
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

        if not self.policy.is_bookable(slot, now=current):
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

        generated = self.generator.generate(start_date, end_date)

        return [
            slot
            for slot in generated
            if self.is_available(slot, now=current)
        ]

    def reserve(
        self,
        slot: Slot,
        *,
        metadata=None,
        now: datetime | None = None,
        series_id: str | None = None,
    ) -> Booking:
        current = (
            now.astimezone(self.generator.timezone)
            if now is not None
            else datetime.now(self.generator.timezone)
        )

        self.policy.validate(slot, now=current)

        booking = Booking(
            slot=slot,
            resource_id=self.resource_id,
            resource_ids=self.resource_ids,
            buffer_before=self.buffer_before,
            buffer_after=self.buffer_after,
            metadata=metadata or {},
            series_id=series_id,
        )
        return self.store.reserve(booking)

    def reserve_first_available(
        self,
        start_date,
        end_date=None,
        *,
        metadata=None,
    ) -> Booking:
        slots = self.available_slots(start_date, end_date)

        for slot in slots:
            try:
                return self.reserve(slot, metadata=metadata)
            except BookingConflictError:
                continue

        raise BookingConflictError(
            "No available slot could be reserved."
        )

    def cancel(
        self,
        booking_id: str,
        *,
        now: datetime | None = None,
    ) -> Booking:
        booking = self.store.get(booking_id)
        if booking.status == "cancelled":
            return booking

        current = (
            now.astimezone(self.generator.timezone)
            if now is not None
            else datetime.now(self.generator.timezone)
        )
        self.policy.validate_cancellation(booking.slot, now=current)
        return self.store.cancel(booking_id)

    def reschedule(
        self,
        booking_id: str,
        new_slot: Slot,
        *,
        now: datetime | None = None,
    ) -> Booking:
        booking = self.store.get(booking_id)
        if booking.status == "cancelled":
            raise SlotUnavailableError(
                "Cancelled bookings cannot be rescheduled."
            )

        current = (
            now.astimezone(self.generator.timezone)
            if now is not None
            else datetime.now(self.generator.timezone)
        )

        self.policy.validate_reschedule(
            booking.slot,
            new_slot,
            now=current,
            rescheduled_count=booking.rescheduled_count,
        )

        candidate = booking.reschedule(new_slot)

        available = self.store.available_capacity(
            candidate,
            capacity=self.capacity,
            exclude_booking_id=booking_id,
        )
        if available <= 0:
            raise BookingConflictError(
                "The requested interval is no longer available."
            )

        return self.store.reschedule(booking_id, new_slot)

    def reserve_recurring(
        self,
        template_slot: Slot,
        rule: RecurrenceRule,
        *,
        metadata=None,
        now: datetime | None = None,
        series_id: str | None = None,
    ) -> list[Booking]:
        """
        Reserve a recurring series using the same local start time and duration.

        If any occurrence cannot be reserved, already-created occurrences
        are cancelled before the error is re-raised.
        """
        series = series_id or str(uuid4())
        local_start = template_slot.start.astimezone(
            self.generator.timezone
        )
        local_time = local_start.timetz().replace(tzinfo=None)
        duration = template_slot.duration
        created: list[Booking] = []

        for occurrence_date in rule.occurrences(local_start.date()):
            candidates = [
                slot
                for slot in self.generator.generate_for_date(occurrence_date)
                if (
                    slot.start.astimezone(self.generator.timezone).time()
                    == local_time
                    and slot.duration == duration
                )
            ]

            if not candidates:
                for booking in created:
                    self.store.cancel(booking.booking_id)
                raise SlotUnavailableError(
                    f"No matching slot exists for {occurrence_date.isoformat()}."
                )

            try:
                booking = self.reserve(
                    candidates[0],
                    metadata=metadata,
                    now=now,
                    series_id=series,
                )
            except Exception:
                for existing in created:
                    self.store.cancel(existing.booking_id)
                raise

            created.append(booking)

        return created

    def upcoming_available(
        self,
        days: int,
        *,
        now: datetime | None = None,
    ) -> list[Slot]:
        current = (
            now.astimezone(self.generator.timezone)
            if now is not None
            else datetime.now(self.generator.timezone)
        )
        return [
            slot
            for slot in self.generator.upcoming(days, now=current)
            if self.is_available(slot, now=current)
        ]
