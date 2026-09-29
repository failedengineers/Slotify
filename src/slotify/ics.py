from __future__ import annotations

from datetime import datetime, timezone
from .booking import Booking


def _escape(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def booking_to_ics(
    booking: Booking,
    *,
    summary: str = "Appointment",
    description: str | None = None,
    location: str | None = None,
) -> str:
    """
    Export a single booking as an RFC 5545-compatible iCalendar event.
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Slotify Scheduling//EN",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{_escape(booking.booking_id)}@slotify",
        f"DTSTAMP:{_utc(booking.created_at)}",
        f"DTSTART:{_utc(booking.slot.start)}",
        f"DTEND:{_utc(booking.slot.end)}",
        f"SUMMARY:{_escape(summary)}",
    ]

    if description:
        lines.append(f"DESCRIPTION:{_escape(description)}")

    if location:
        lines.append(f"LOCATION:{_escape(location)}")

    lines.extend([
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ])
    return "\r\n".join(lines)
