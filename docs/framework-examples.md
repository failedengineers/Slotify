# Framework Examples

Slotify is framework-independent. These patterns show where it fits.

## Django / DRF

Use Slotify in a service layer and return serialized Slot or Booking values from your API.

~~~python
def available_slots(provider, date):
    engine = get_provider_engine(provider)
    return engine.available_slots(date)
~~~

See the Django integration guide for a complete example.

## FastAPI

The same service can be called from a FastAPI route:

~~~python
from fastapi import FastAPI

app = FastAPI()

@app.get("/providers/{provider_id}/slots")
def slots(provider_id: str, date: str):
    engine = get_provider_engine(provider_id)
    return [slot.to_dict() for slot in engine.available_slots(date)]
~~~

FastAPI owns HTTP, authentication, dependency injection, and persistence. Slotify owns scheduling rules.

## Flask

A Flask route can use the same service:

~~~python
@app.get("/providers/<provider_id>/slots")
def slots(provider_id):
    engine = get_provider_engine(provider_id)
    return {"slots": [slot.to_dict() for slot in engine.available_slots(request.args["date"])]}
~~~

No framework integration package is required.
