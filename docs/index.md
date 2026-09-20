# Slotify Scheduling

**Timezone-aware scheduling and appointment slot engine for Python.**

## Install

~~~bash
pip install slotify-scheduling
~~~

## First example

~~~python
from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate("2026-09-21", "2026-09-21")
~~~

## Learn by task

- [Getting Started](getting-started.md)
- [Django Integration](django.md)
- [Timezone & DST](timezones.md)
- [Recipes](recipes.md)
- [API Guide](api.md)
