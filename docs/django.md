# Django / DRF Integration

Slotify is a scheduling library, not a Django app. You do not need to add slotify to INSTALLED_APPS.

## Install

~~~bash
python -m pip install slotify-scheduling
~~~

## Recommended architecture

~~~text
Django models -> service layer -> SlotGenerator -> AvailabilityEngine -> Django/DRF API
~~~

Keep provider and business data in Django. Create Slotify objects in a service layer so scheduling rules are not duplicated across views.

## Example provider model

~~~python
from django.db import models

class Provider(models.Model):
    name = models.CharField(max_length=200)
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    work_start = models.TimeField()
    work_end = models.TimeField()
    slot_duration = models.PositiveIntegerField(default=30)
~~~

Store the provider timezone explicitly.

## Build an engine

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

## Django JSON endpoint

~~~python
from django.http import JsonResponse, Http404
from .models import Provider
from .services import get_provider_engine

def available_slots(request, provider_id):
    try:
        provider = Provider.objects.get(pk=provider_id)
    except Provider.DoesNotExist:
        raise Http404

    engine = get_provider_engine(provider)
    date_value = request.GET.get("date", "2026-10-05")
    slots = engine.available_slots(date_value)

    return JsonResponse({
        "provider_id": provider.pk,
        "slots": [slot.to_dict() for slot in slots],
    })
~~~

A production endpoint should validate incoming dates and authenticate requests where required.

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
        date_value = request.query_params.get("date", "2026-10-05")
        slots = engine.available_slots(date_value)
        return Response({
            "provider_id": provider.pk,
            "slots": [slot.to_dict() for slot in slots],
        })
~~~

## Typical booking API

~~~text
GET  /providers/<id>/availability?date=2026-10-05
POST /providers/<id>/bookings
POST /bookings/<id>/cancel
POST /bookings/<id>/reschedule
~~~

The exact URLs are your application's responsibility.

## Booking request flow

1. Authenticate the user.
2. Load the provider/resource.
3. Reconstruct the scheduling engine.
4. Identify the requested slot.
5. Call reserve().
6. Persist application-specific booking/customer data.
7. Trigger payment or notification logic if required.

Do not trust a price, provider, or authorization decision supplied only by the client.

## Django database storage

Your Django application can keep a booking model containing fields such as:

~~~text
id
customer
provider
slot_start
slot_end
status
slotify_booking_id
metadata
created_at
~~~

The application database should remain the source of truth for durable business records.

## Production BookingStore

For multiple workers, implement BookingStore using your transactional database. The important operations are reserve(), cancel(), reschedule(), get(), list(), and available_capacity(). The database implementation must handle concurrent reservations atomically.

## In-memory store warning

InMemoryBookingStore is thread-safe inside one Python process. It is not shared between multiple Gunicorn workers, containers, servers, or separate processes. Use durable storage for those deployments.

## API response example

~~~json
{
  "start": "2026-10-05T09:00:00+05:30",
  "end": "2026-10-05T09:30:00+05:30",
  "duration_seconds": 1800,
  "timezone": "Asia/Kolkata"
}
~~~
