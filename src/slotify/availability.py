from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4

from .booking import Booking, BookingStore, InMemoryBookingStore
from .exceptions import BookingConflictError, SlotUnavailableError, HoldExpiredError
from .holds import BookingHold, HoldStore, InMemoryHoldStore
from .generator import SlotGenerator
from .models import Slot
from .policy import BookingPolicy
from .recurrence import RecurrenceRule


@dataclass(frozen=True, slots=True)
class AvailabilityResult:
    """Explain whether a slot can currently be booked."""

    slot: Slot
    available: bool
    reason: str | None = None
    resource_id: str | None = None
    code: str | None = None


class AvailabilityEngine:
    """
    Converts generated slots into bookable availability.

    Handles bookings, capacity, buffers, resources, resource pools,
    booking policies, availability explanations, recurrence,
    cancellation and rescheduling.
    """

    def __init__(
        self,
        generator: SlotGenerator,
        *,
        store: BookingStore | None = None,
        resource_id: str | None = None,
        resource_ids: tuple[str, ...] | list[str] | None = None,
        resource_pool: tuple[str, ...] | list[str] | None = None,
        capacity: int = 1,
        buffer_before: int | timedelta = 0,
        buffer_after: int | timedelta = 0,
        policy: BookingPolicy | None = None,
        schedules: Mapping[str, SlotGenerator] | None = None,
        default_schedule: str = "default",
        resource_strategy: str = "first_available",
        hold_store: HoldStore | None = None,
    ) -> None:
        self.policy = policy if policy is not None else BookingPolicy()

        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, int)
            or capacity < 1
        ):
            raise ValueError("capacity must be a positive integer.")

        resources = tuple(resource_ids or ())
        pool = tuple(resource_pool or ())

        if pool and (resource_id is not None or resources):
            raise ValueError(
                "resource_pool cannot be combined with resource_id or resource_ids."
            )

        if pool:
            if any(
                not isinstance(value, str) or not value.strip()
                for value in pool
            ):
                raise ValueError(
                    "resource_pool must contain non-empty strings."
                )
            if len(set(pool)) != len(pool):
                raise ValueError("resource_pool cannot contain duplicates.")

        if resource_id is not None and resource_id not in resources:
            resources = (resource_id, *resources)

        if not resources:
            resources = (resource_id,) if resource_id is not None else ()

        self.generator = generator
        schedule_map: dict[str, SlotGenerator] = {"default": generator}
        if schedules:
            schedule_map.update(dict(schedules))

        for name, value in schedule_map.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Schedule names must be non-empty strings.")
            if not isinstance(value, SlotGenerator):
                raise TypeError("All schedules must be SlotGenerator instances.")

        if default_schedule not in schedule_map:
            raise ValueError(
                f"Unknown default schedule: {default_schedule!r}."
            )

        base_timezone = self._timezone_key(generator.timezone)
        for value in schedule_map.values():
            if self._timezone_key(value.timezone) != base_timezone:
                raise ValueError(
                    "All availability schedules must use the same timezone."
                )

        self.schedules = MappingProxyType(schedule_map)
        self.default_schedule = default_schedule
        self.resource_id = resource_id
        self.resource_ids = resources
        self.resource_pool = pool
        if resource_strategy not in {"first_available", "round_robin", "least_loaded"}:
            raise ValueError("resource_strategy must be 'first_available', 'round_robin', or 'least_loaded'.")
        self.resource_strategy = resource_strategy
        self._resource_cursor = 0
        self.capacity = capacity
        self.store = (
            store
            if store is not None
            else InMemoryBookingStore(capacity=capacity)
        )
        self.buffer_before = self._duration(buffer_before, "buffer_before")
        self.buffer_after = self._duration(buffer_after, "buffer_after")
        self.hold_store = hold_store if hold_store is not None else InMemoryHoldStore()

    @classmethod
    def from_schedules(
        cls,
        schedules: Mapping[str, SlotGenerator],
        *,
        default_schedule: str,
        **kwargs,
    ) -> "AvailabilityEngine":
        """Create an engine from multiple named SlotGenerator profiles."""
        if not schedules:
            raise ValueError("schedules must contain at least one profile.")
        if default_schedule not in schedules:
            raise ValueError(
                f"Unknown default schedule: {default_schedule!r}."
            )
        generator = schedules[default_schedule]
        return cls(
            generator,
            schedules=schedules,
            default_schedule=default_schedule,
            **kwargs,
        )

    @staticmethod
    def _timezone_key(value) -> str:
        return getattr(value, "key", str(value))

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

    @staticmethod
    def _date(value) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(
                    "Dates must use YYYY-MM-DD format."
                ) from exc
        raise TypeError(
            "Date values must be date, datetime, or YYYY-MM-DD strings."
        )

    def _generator_for(self, schedule_name: str | None) -> SlotGenerator:
        name = schedule_name or self.default_schedule
        try:
            return self.schedules[name]
        except KeyError as exc:
            raise ValueError(
                f"Unknown schedule: {name!r}. "
                f"Available schedules: {', '.join(self.schedules)}."
            ) from exc

    def schedule_names(self) -> tuple[str, ...]:
        """Return the configured availability profile names."""
        return tuple(self.schedules)

    def _current(
        self,
        now: datetime | None,
        generator: SlotGenerator,
    ) -> datetime:
        if now is None:
            return datetime.now(generator.timezone)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware.")
        return now.astimezone(generator.timezone)

    def _booking_for(
        self,
        slot: Slot,
        *,
        resource_id: str | None = None,
        resource_ids: tuple[str, ...] | None = None,
        metadata=None,
        series_id: str | None = None,
    ) -> Booking:
        return Booking(
            slot=slot,
            resource_id=(
                self.resource_id
                if resource_id is None and resource_ids is None
                else resource_id
            ),
            resource_ids=(
                self.resource_ids
                if resource_ids is None and resource_id is None
                else (resource_ids or ())
            ),
            buffer_before=self.buffer_before,
            buffer_after=self.buffer_after,
            metadata=metadata or {},
            series_id=series_id,
        )

    def _scope_bookings(self) -> list[Booking]:
        if not self.resource_ids and not self.resource_pool:
            return self.store.list()

        resource_ids = (
            self.resource_pool
            if self.resource_pool
            else self.resource_ids
        )
        found: dict[str, Booking] = {}
        for resource_id in resource_ids:
            for booking in self.store.list(resource_id=resource_id):
                found[booking.booking_id] = booking
        return sorted(
            found.values(),
            key=lambda booking: booking.protected_start,
        )

    def _validate_limits(
        self,
        slot: Slot,
        *,
        now: datetime,
    ) -> None:
        active = [
            booking
            for booking in self._scope_bookings()
            if booking.status == "confirmed"
        ]

        now_utc = now.astimezone(timezone.utc)
        local_start = slot.start.astimezone(now.tzinfo)
        candidate_date = local_start.date()
        candidate_week = local_start.isocalendar()[:2]

        daily = [
            booking
            for booking in active
            if booking.slot.start.astimezone(now.tzinfo).date() == candidate_date
        ]
        if (
            self.policy.max_bookings_per_day is not None
            and len(daily) >= self.policy.max_bookings_per_day
        ):
            raise SlotUnavailableError(
                "The maximum number of bookings for this day has been reached."
            )

        weekly = [
            booking
            for booking in active
            if booking.slot.start.astimezone(now.tzinfo).isocalendar()[:2]
            == candidate_week
        ]
        if (
            self.policy.max_bookings_per_week is not None
            and len(weekly) >= self.policy.max_bookings_per_week
        ):
            raise SlotUnavailableError(
                "The maximum number of bookings for this week has been reached."
            )

        upcoming = [
            booking
            for booking in active
            if booking.slot.start_utc >= now_utc
        ]
        if (
            self.policy.max_upcoming_bookings is not None
            and len(upcoming) >= self.policy.max_upcoming_bookings
        ):
            raise SlotUnavailableError(
                "The maximum number of upcoming bookings has been reached."
            )

        gap = self.policy.min_gap_between_bookings
        if gap > timedelta(0):
            candidate_start = slot.start_utc
            candidate_end = slot.end_utc
            for booking in active:
                existing_start = booking.protected_start.astimezone(timezone.utc)
                existing_end = booking.protected_end.astimezone(timezone.utc)
                if (
                    candidate_start < existing_end + gap
                    and candidate_end + gap > existing_start
                ):
                    raise SlotUnavailableError(
                        "The slot does not satisfy the minimum gap between bookings."
                    )

    def _ordered_pool_resources(self, slot: Slot, *, advance: bool = False) -> tuple[str, ...]:
        if not self.resource_pool:
            return ()
        resources = list(self.resource_pool)
        if self.resource_strategy == "first_available":
            return tuple(resources)
        if self.resource_strategy == "round_robin":
            offset = self._resource_cursor % len(resources)
            if advance:
                self._resource_cursor = (self._resource_cursor + 1) % len(resources)
            return tuple(resources[offset:] + resources[:offset])

        def load(resource_id: str) -> int:
            return sum(
                1
                for booking in self.store.list(resource_id=resource_id)
                if booking.status == "confirmed"
                and booking.protected_start < slot.end
                and slot.start < booking.protected_end
            )
        return tuple(sorted(resources, key=lambda item: (load(item), resources.index(item))))

    def _candidate(
        self,
        slot: Slot,
        *,
        resource_id: str | None = None,
        metadata=None,
        series_id: str | None = None,
    ) -> Booking:
        if resource_id is not None:
            return self._booking_for(
                slot,
                resource_id=resource_id,
                metadata=metadata,
                series_id=series_id,
            )
        return self._booking_for(
            slot,
            metadata=metadata,
            series_id=series_id,
        )

    def _check_availability(
        self,
        slot: Slot,
        *,
        now: datetime,
        resource_selection: bool,
    ) -> AvailabilityResult:
        try:
            self.policy.validate(slot, now=now)
            self._validate_limits(slot, now=now)
        except SlotUnavailableError as exc:
            return AvailabilityResult(
                slot=slot,
                available=False,
                reason=str(exc),
                code="policy",
            )

        if self.resource_pool:
            for resource_id in self._ordered_pool_resources(slot):
                candidate = self._candidate(slot, resource_id=resource_id)
                if self.hold_store.conflicts(candidate, now=now):
                    continue
                if (
                    self.store.available_capacity(
                        candidate,
                        capacity=self.capacity,
                    )
                    > 0
                ):
                    return AvailabilityResult(
                        slot=slot,
                        available=True,
                        resource_id=resource_id,
                        code="available",
                    )
            return AvailabilityResult(
                slot=slot,
                available=False,
                reason="No resource in the resource pool is available.",
            code="resource_unavailable",
            )

        candidate = self._candidate(slot)
        if self.hold_store.conflicts(candidate, now=now):
            return AvailabilityResult(
                slot=slot,
                available=False,
                reason="The requested slot is temporarily held.",
                code="hold_conflict",
            )
        if (
            self.store.available_capacity(
                candidate,
                capacity=self.capacity,
            )
            > 0
        ):
            return AvailabilityResult(
                slot=slot,
                available=True,
                resource_id=(
                    self.resource_ids[0]
                    if len(self.resource_ids) == 1
                    else self.resource_id
                ),
                code="available",
            )

        return AvailabilityResult(
            slot=slot,
            available=False,
            reason="The requested slot is at capacity or conflicts with an existing booking.",
            code="capacity_conflict",
        )

    def check_availability(
        self,
        slot: Slot,
        *,
        now: datetime | None = None,
    ) -> AvailabilityResult:
        """Return a structured explanation of a slot's current availability."""
        current = self._current(now, self.generator)
        return self._check_availability(
            slot,
            now=current,
            resource_selection=True,
        )

    def is_available(
        self,
        slot: Slot,
        *,
        now: datetime | None = None,
    ) -> bool:
        return self.check_availability(slot, now=now).available

    def available_slots(
        self,
        start_date,
        end_date=None,
        *,
        now: datetime | None = None,
        schedule_name: str | None = None,
        limit: int | None = None,
    ) -> list[Slot]:
        """Return bookable slots, scanning one day at a time to reduce memory use."""
        generator = self._generator_for(schedule_name)
        current = self._current(now, generator)
        start = self._date(start_date)
        end = self._date(
            end_date if end_date is not None else start_date
        )
        if end < start:
            raise ValueError("end_date must be greater than or equal to start_date.")
        if limit is not None and (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
        ):
            raise ValueError("limit must be a positive integer or None.")

        result: list[Slot] = []
        day = start
        while day <= end:
            for slot in generator.generate_for_date(day):
                if self._check_availability(
                    slot,
                    now=current,
                    resource_selection=True,
                ).available:
                    result.append(slot)
                    if limit is not None and len(result) >= limit:
                        return result
            day += timedelta(days=1)
        return result

    def next_available(
        self,
        start_date,
        end_date=None,
        *,
        now: datetime | None = None,
        schedule_name: str | None = None,
    ) -> Slot | None:
        """Return the first bookable slot in the requested date range."""
        slots = self.available_slots(
            start_date,
            end_date,
            now=now,
            schedule_name=schedule_name,
            limit=1,
        )
        return slots[0] if slots else None

    def available_between(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        *,
        now: datetime | None = None,
        schedule_name: str | None = None,
        limit: int | None = None,
    ) -> list[Slot]:
        """Return bookable slots fully contained inside an exact datetime range."""
        if (
            start_datetime.tzinfo is None
            or start_datetime.utcoffset() is None
            or end_datetime.tzinfo is None
            or end_datetime.utcoffset() is None
        ):
            raise ValueError(
                "start_datetime and end_datetime must be timezone-aware."
            )
        if end_datetime.astimezone(timezone.utc) <= start_datetime.astimezone(timezone.utc):
            raise ValueError("end_datetime must be after start_datetime.")
        if limit is not None and (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
        ):
            raise ValueError("limit must be a positive integer or None.")

        generator = self._generator_for(schedule_name)
        current = self._current(now, generator)
        start = start_datetime.astimezone(generator.timezone)
        end = end_datetime.astimezone(generator.timezone)

        result: list[Slot] = []
        day = start.date()
        while day <= end.date():
            for slot in generator.generate_for_date(day):
                if (
                    slot.start_utc >= start.astimezone(timezone.utc)
                    and slot.end_utc <= end.astimezone(timezone.utc)
                    and self._check_availability(
                        slot,
                        now=current,
                        resource_selection=True,
                    ).available
                ):
                    result.append(slot)
                    if limit is not None and len(result) >= limit:
                        return result
            day += timedelta(days=1)
        return result

    def _generator_with_duration(
        self,
        generator: SlotGenerator,
        duration: int | timedelta,
    ) -> SlotGenerator:
        kwargs = dict(
            duration=duration,
            interval=generator.interval,
            timezone=generator.timezone,
            breaks=generator.breaks,
            excluded_dates=generator.excluded_dates,
            dst_ambiguous=generator.dst_ambiguous,
            dst_nonexistent=generator.dst_nonexistent,
        )
        if generator.schedule is not None:
            kwargs["schedule"] = generator.schedule
        else:
            kwargs["windows"] = generator.windows
            kwargs["weekdays"] = generator.weekdays
        return SlotGenerator(**kwargs)

    def available_for_duration(
        self,
        duration: int | timedelta,
        start_date,
        end_date=None,
        *,
        now: datetime | None = None,
        schedule_name: str | None = None,
        limit: int | None = None,
    ) -> list[Slot]:
        """Generate and return bookable slots for a requested appointment duration."""
        generator = self._generator_for(schedule_name)
        duration_generator = self._generator_with_duration(
            generator,
            duration,
        )
        current = self._current(now, duration_generator)
        start = self._date(start_date)
        end = self._date(
            end_date if end_date is not None else start_date
        )
        if end < start:
            raise ValueError("end_date must be greater than or equal to start_date.")
        if limit is not None and (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
        ):
            raise ValueError("limit must be a positive integer or None.")

        result: list[Slot] = []
        day = start
        while day <= end:
            for slot in duration_generator.generate_for_date(day):
                if self._check_availability(
                    slot,
                    now=current,
                    resource_selection=True,
                ).available:
                    result.append(slot)
                    if limit is not None and len(result) >= limit:
                        return result
            day += timedelta(days=1)
        return result

    def hold(
        self,
        slot: Slot,
        *,
        expires_at: datetime,
        metadata=None,
        now: datetime | None = None,
        schedule_name: str | None = None,
    ) -> BookingHold:
        """Temporarily hold a slot until expires_at."""
        generator = self._generator_for(schedule_name)
        current = self._current(now, generator)
        if expires_at.tzinfo is None or expires_at.utcoffset() is None:
            raise ValueError("expires_at must be timezone-aware.")
        if expires_at <= current:
            raise ValueError("expires_at must be in the future.")
        self.policy.validate(slot, now=current)
        if self.resource_pool:
            for resource_id in self._ordered_pool_resources(slot):
                candidate = self._candidate(slot, resource_id=resource_id)
                if self.store.available_capacity(candidate, capacity=self.capacity) <= 0:
                    continue
                if self.hold_store.conflicts(candidate, now=current):
                    continue
                return self.hold_store.create(BookingHold(
                    slot=slot, expires_at=expires_at,
                    resource_id=resource_id, metadata=metadata or {},
                ))
            raise BookingConflictError("No resource in the resource pool is available for the hold.")
        candidate = self._candidate(slot, metadata=metadata)
        if self.store.available_capacity(candidate, capacity=self.capacity) <= 0:
            raise BookingConflictError("The requested interval is no longer available.")
        if self.hold_store.conflicts(candidate, now=current):
            raise BookingConflictError("The requested slot is already held.")
        return self.hold_store.create(BookingHold(
            slot=slot, expires_at=expires_at, metadata=metadata or {}
        ))

    def confirm_hold(
        self,
        hold_id: str,
        *,
        metadata=None,
        now: datetime | None = None,
    ) -> Booking:
        """Convert an active hold into a confirmed booking."""
        current = self._current(now, self.generator)
        hold = self.hold_store.get(hold_id, now=current)
        booking = self._candidate(
            hold.slot,
            resource_id=hold.resource_id,
            metadata=metadata if metadata is not None else hold.metadata,
        )
        if self.hold_store.conflicts(booking, now=current, exclude_hold_id=hold_id):
            raise BookingConflictError("The requested slot is blocked by another hold.")
        confirmed = self.store.reserve(booking)
        self.hold_store.release(hold_id)
        return confirmed

    def release_hold(self, hold_id: str) -> BookingHold:
        """Release a temporary hold without creating a booking."""
        return self.hold_store.release(hold_id)

    def reserve(
        self,
        slot: Slot,
        *,
        metadata=None,
        now: datetime | None = None,
        series_id: str | None = None,
        idempotency_key: str | None = None,
        schedule_name: str | None = None,
    ) -> Booking:
        generator = self._generator_for(schedule_name)
        current = self._current(now, generator)

        self.policy.validate(slot, now=current)
        self._validate_limits(slot, now=current)

        if idempotency_key is not None:
            if not isinstance(idempotency_key, str) or not idempotency_key.strip():
                raise ValueError("idempotency_key must be a non-empty string or None.")
            finder = getattr(self.store, "find_by_idempotency_key", None)
            if finder is not None:
                existing = finder(idempotency_key)
                if existing is not None:
                    return existing

        if self.resource_pool:
            last_error: BookingConflictError | None = None
            for resource_id in self._ordered_pool_resources(
                slot,
                advance=self.resource_strategy == "round_robin",
            ):
                booking = self._candidate(
                    slot,
                    resource_id=resource_id,
                    metadata=metadata,
                    series_id=series_id,
                )
                if idempotency_key is not None:
                    booking = Booking(
                        slot=booking.slot,
                        resource_id=booking.resource_id,
                        booking_id=booking.booking_id,
                        status=booking.status,
                        buffer_before=booking.buffer_before,
                        buffer_after=booking.buffer_after,
                        created_at=booking.created_at,
                        metadata=booking.metadata,
                        resource_ids=booking.resource_ids,
                        series_id=booking.series_id,
                        rescheduled_count=booking.rescheduled_count,
                        idempotency_key=idempotency_key,
                    )
                try:
                    if self.hold_store.conflicts(booking, now=current):
                        last_error = BookingConflictError("The requested slot is temporarily held.")
                        continue
                    return self.store.reserve(booking)
                except BookingConflictError as exc:
                    last_error = exc
            raise BookingConflictError(
                "No resource in the resource pool is available."
            ) from last_error

        if idempotency_key is not None:
            if not isinstance(idempotency_key, str) or not idempotency_key.strip():
                raise ValueError("idempotency_key must be a non-empty string or None.")
            finder = getattr(self.store, "find_by_idempotency_key", None)
            if finder is not None:
                existing = finder(idempotency_key)
                if existing is not None:
                    return existing
        booking = self._booking_for(
            slot,
            metadata=metadata,
            series_id=series_id,
        )
        if idempotency_key is not None:
            booking = Booking(
                slot=booking.slot,
                resource_id=booking.resource_id,
                booking_id=booking.booking_id,
                status=booking.status,
                buffer_before=booking.buffer_before,
                buffer_after=booking.buffer_after,
                created_at=booking.created_at,
                metadata=booking.metadata,
                resource_ids=booking.resource_ids,
                series_id=booking.series_id,
                rescheduled_count=booking.rescheduled_count,
                idempotency_key=idempotency_key,
            )
        if self.hold_store.conflicts(booking, now=current):
            raise BookingConflictError("The requested slot is temporarily held.")
        return self.store.reserve(booking)

    def reserve_first_available(
        self,
        start_date,
        end_date=None,
        *,
        metadata=None,
        schedule_name: str | None = None,
    ) -> Booking:
        slots = self.available_slots(
            start_date,
            end_date,
            schedule_name=schedule_name,
        )

        for slot in slots:
            try:
                return self.reserve(
                    slot,
                    metadata=metadata,
                    schedule_name=schedule_name,
                )
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

        current = self._current(now, self.generator)
        self.policy.validate_cancellation(
            booking.slot,
            now=current,
        )
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

        current = self._current(now, self.generator)

        self.policy.validate_reschedule(
            booking.slot,
            new_slot,
            now=current,
            rescheduled_count=booking.rescheduled_count,
        )
        self._validate_limits(new_slot, now=current)

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
        schedule_name: str | None = None,
    ) -> list[Booking]:
        """Reserve a recurring series using the same local start time and duration."""
        series = series_id or str(uuid4())
        generator = self._generator_for(schedule_name)
        local_start = template_slot.start.astimezone(generator.timezone)
        local_time = local_start.timetz().replace(tzinfo=None)
        duration = template_slot.duration
        created: list[Booking] = []

        for occurrence_date in rule.occurrences(local_start.date()):
            candidates = [
                slot
                for slot in generator.generate_for_date(occurrence_date)
                if (
                    slot.start.astimezone(generator.timezone).time()
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
                    schedule_name=schedule_name,
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
        schedule_name: str | None = None,
        limit: int | None = None,
    ) -> list[Slot]:
        generator = self._generator_for(schedule_name)
        current = self._current(now, generator)

        if limit is not None and (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
        ):
            raise ValueError("limit must be a positive integer or None.")

        result: list[Slot] = []
        start = current.date()
        end = start + timedelta(days=days - 1)
        for slot in self.available_slots(
            start,
            end,
            now=current,
            schedule_name=schedule_name,
        ):
            if slot.start_utc >= current.astimezone(timezone.utc):
                result.append(slot)
                if limit is not None and len(result) >= limit:
                    break
        return result
