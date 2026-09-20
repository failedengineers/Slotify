from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate(
    "2026-09-21",
    "2026-09-21",
)

for slot in slots:
    print(slot.start, "->", slot.end)
