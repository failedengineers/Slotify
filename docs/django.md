# Django Integration

Slotify works as a scheduling layer inside Django and Django REST Framework. It does not need to be added to `INSTALLED_APPS`.

## Install

~~~bash
pip install slotify-scheduling
~~~

## Example model

~~~python
from django.db import models

class Provider(models.Model):
    name = models.CharField(max_length=200)
    work_start = models.TimeField()
    work_end = models.TimeField()
    slot_duration = models.PositiveIntegerField(default=30)
    timezone = models.CharField(
        max_length=64,
        default="Asia/Kolkata",
    )
~~~

Your database remains the source of truth for provider/application data.

## Service layer

~~~python
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
~~~

Keeping this in a service module prevents scheduling code from being duplicated across views.

## Django JSON endpoint

~~~python
from django.http import JsonResponse
from .models import Provider
from .services import get_provider_engine

def available_slots(request, provider_id):
    provider = Provider.objects.get(pk=provider_id)
    engine = get_provider_engine(provider)

    slots = engine.available_slots("2026-09-21")

    return JsonResponse({
        "provider_id": provider.pk,
        "slots": [slot.to_dict() for slot in slots],
    })
~~~

## Django REST Framework

~~~python
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Provider
from .services import get_provider_engine

class ProviderAvailabilityView(APIView):
    def get(self, request, provider_id):
        provider = Provider.objects.get(pk=provider_id)
        engine = get_provider_engine(provider)

        slots = engine.available_slots("2026-09-21")

        return Response({
            "provider_id": provider.pk,
            "slots": [slot.to_dict() for slot in slots],
        })
~~~

## Booking workflow

A real application commonly looks like:

~~~text
Frontend
   |
   v
Django / DRF
   |
   +--> authenticate user
   |
   +--> load provider/resource
   |
   +--> ask Slotify for availability
   |
   +--> user selects a slot
   |
   +--> application booking transaction
   |
   +--> payment (if required)
   |
   +--> notification
~~~

Slotify handles scheduling concerns. Django remains responsible for application concerns.

## Production storage

The built-in `InMemoryBookingStore` is useful for tests and simple single-process applications.

For multi-worker or distributed Django deployments, implement/use a `BookingStore` backed by your transactional database and make the application-level reservation workflow safe under concurrent requests.

Do not use in-memory state as the shared source of truth across multiple workers.

## A useful provider pattern

Store the provider's timezone explicitly rather than assuming the server timezone:

~~~python
Provider(
    timezone="Asia/Kolkata",
)
~~~

Then pass that timezone into `SlotGenerator`.
