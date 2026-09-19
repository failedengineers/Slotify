class SlotifyError(Exception):
    """Base exception for all Slotify errors."""


class ConfigurationError(SlotifyError, ValueError):
    """Raised when scheduler configuration is invalid."""


class InvalidTimeError(ConfigurationError):
    """Raised when a supplied time value is invalid."""


class InvalidDateRangeError(ConfigurationError):
    """Raised when a supplied date range is invalid."""


class InvalidTimezoneError(ConfigurationError):
    """Raised when a timezone cannot be loaded."""


class DSTTransitionError(ConfigurationError):
    """Raised when a local datetime is invalid or ambiguous because of DST."""


class SlotConflictError(SlotifyError):
    """Raised when a slot conflicts with another reservation or rule."""

class BookingError(SlotifyError):
    """Base exception for booking-related errors."""


class BookingConflictError(BookingError, SlotConflictError):
    """Raised when a booking conflicts with existing capacity."""


class BookingNotFoundError(BookingError):
    """Raised when a requested booking does not exist."""

class SlotUnavailableError(SlotifyError):
    """Raised when a slot cannot currently be booked."""