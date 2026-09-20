# Example service layer for Django.
# Keep scheduling in Slotify and application persistence in Django.

from slotify import AvailabilityEngine, SlotGenerator


def get_provider_engine(provider):
    generator = SlotGenerator(
        start=provider.work_start.strftime("%H:%M"),
        end=provider.work_end.strftime("%H:%M"),
        duration=provider.slot_duration,
        timezone=provider.timezone,
    )

    return AvailabilityEngine(
        generator,
        resource_id=str(provider.pk),
        capacity=1,
    )


def get_slots(provider, date):
    engine = get_provider_engine(provider)
    return engine.available_slots(date)
