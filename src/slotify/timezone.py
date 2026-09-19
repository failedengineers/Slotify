from __future__ import annotations

from datetime import date, datetime, time, timezone, tzinfo
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .exceptions import DSTTransitionError, InvalidTimezoneError


AmbiguousPolicy = Literal["earlier", "later", "raise"]


def get_timezone(value: str | tzinfo) -> tzinfo:
    """
    Resolve an IANA timezone name or accept an existing tzinfo.
    """

    if isinstance(value, str):
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise InvalidTimezoneError(
                f"Unknown IANA timezone: {value!r}"
            ) from exc

    if isinstance(value, tzinfo):
        return value

    raise InvalidTimezoneError(
        "timezone must be an IANA timezone string "
        "or tzinfo instance."
    )


def ensure_aware(
    value: datetime,
    name: str = "datetime",
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{name} must be timezone-aware."
        )

    return value


def to_utc(value: datetime) -> datetime:
    return ensure_aware(value).astimezone(timezone.utc)


def convert_timezone(
    value: datetime,
    tz: str | tzinfo,
) -> datetime:
    return ensure_aware(value).astimezone(
        get_timezone(tz)
    )


def _candidate(
    naive: datetime,
    tz: tzinfo,
    fold: int,
) -> datetime:
    return naive.replace(
        tzinfo=tz,
        fold=fold,
    )


def _round_trip(
    candidate: datetime,
    tz: tzinfo,
) -> datetime:
    return (
        candidate
        .astimezone(timezone.utc)
        .astimezone(tz)
        .replace(tzinfo=None)
    )


def local_datetime_candidates(
    value: date | datetime,
    local_time: time | None,
    tz: str | tzinfo,
) -> tuple[datetime, ...]:
    """
    Resolve a local wall-clock datetime.

    Returns:
        one datetime for a normal time
        two datetimes for an ambiguous fall-back time

    Raises:
        DSTTransitionError for a nonexistent spring-forward time.
    """

    zone = get_timezone(tz)

    if isinstance(value, datetime):
        if local_time is not None:
            raise ValueError(
                "local_time must be omitted when value is a datetime."
            )

        if value.tzinfo is not None:
            return (value.astimezone(zone),)

        naive = value

    elif isinstance(value, date):
        if local_time is None:
            raise ValueError(
                "local_time is required when value is a date."
            )

        if local_time.tzinfo is not None:
            raise ValueError(
                "local_time must be timezone-naive."
            )

        naive = datetime.combine(value, local_time)

    else:
        raise TypeError(
            "value must be a date or datetime."
        )

    candidate_0 = _candidate(naive, zone, 0)
    candidate_1 = _candidate(naive, zone, 1)

    valid_0 = (
        _round_trip(candidate_0, zone) == naive
    )
    valid_1 = (
        _round_trip(candidate_1, zone) == naive
    )

    # Spring-forward gap.
    if not valid_0 and not valid_1:
        raise DSTTransitionError(
            f"{naive.isoformat()} does not exist in "
            f"timezone "
            f"{getattr(zone, 'key', zone)!s}."
        )

    # Fall-back repeated hour.
    if (
        valid_0
        and valid_1
        and candidate_0.utcoffset()
        != candidate_1.utcoffset()
    ):
        return candidate_0, candidate_1

    return (candidate_0 if valid_0 else candidate_1,)


def resolve_local_datetime(
    value: date | datetime,
    local_time: time | None,
    tz: str | tzinfo,
    *,
    ambiguous: AmbiguousPolicy = "raise",
) -> datetime:
    candidates = local_datetime_candidates(
        value,
        local_time,
        tz,
    )

    if len(candidates) == 1:
        return candidates[0]

    if ambiguous == "raise":
        zone = get_timezone(tz)

        raise DSTTransitionError(
            f"Ambiguous local time in timezone "
            f"{getattr(zone, 'key', zone)!s}; "
            "choose ambiguous='earlier' or "
            "ambiguous='later'."
        )

    if ambiguous not in {"earlier", "later"}:
        raise ValueError(
            "ambiguous must be 'earlier', "
            "'later', or 'raise'."
        )

    ordered = sorted(
        candidates,
        key=to_utc,
    )

    return (
        ordered[0]
        if ambiguous == "earlier"
        else ordered[-1]
    )