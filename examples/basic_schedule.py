from slotify import SlotGenerator

generator = SlotGenerator(
    start="09:00",
    end="17:00",
    duration=30,
    timezone="Asia/Kolkata",
)

slots = generator.generate("2026-10-05")

assert slots
assert slots[0].start.hour == 9

for slot in slots[:3]:
    print(slot.start, "->", slot.end)
