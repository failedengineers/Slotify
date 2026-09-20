# Django Integration

Slotify works well as a scheduling layer inside Django. It does not need to be added to INSTALLED_APPS.

## Install

~~~bash
pip install slotify-scheduling
~~~

## Example provider model

~~~python
from django.db import models

class Provider(models.Model):
    name = models.CharField(max_length=200)
    work_start = models.TimeField()
    work_end = models.TimeField()
    slot_duration = models.PositiveIntegerField(default=30)
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
~~~

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

## JSON endpoint

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

## Booking

For a test or single-process application:

~~~python
available = engine.available_slots("2026-09-21")

if available:
    booking = engine.reserve(available[0])
~~~

For multi-worker production systems, do not rely on in-memory booking state as the shared source of truth.

Implement BookingStore against your transactional storage and make the application-level booking operation safe under concurrent requests.

## Real appointment architecture

~~~text
Browser / Mobile App
        |
        v
Django / DRF
        |
        v
Provider + application DB
        |
        v
Slotify availability
        |
        v
User selects slot
        |
        v
Transactional booking workflow
        |
        +--> Payment
        |
        +--> Notification
~~~

Slotify focuses on scheduling. Django remains responsible for authentication, permissions, persistence, payments, and application-specific workflows.
