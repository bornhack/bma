"""Managers for the hitcounter.

Most of this code is originally borrowed from https://github.com/thornomad/django-hitcount/
"""

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone


class HitManager(models.Manager):  # type: ignore[type-arg]
    """Default manager for the Hit model."""

    def filter_active(self, *args: str, **kwargs: dict[str, str]) -> models.QuerySet[Any]:
        """Return only the 'active' hits.

        How you count a hit/view will depend on personal choice: Should the
        same user/visitor *ever* be counted twice?  After a week, or a month,
        or a year, should their view be counted again?

        The default is to consider a visitor's hit still 'active' if they
        return within a the last seven days..  After that the hit
        will be counted again.  So if one person visits once a week for a year,
        they will add 52 hits to a given object.

        Change how long the expiration is by adding to settings.py:

        HITCOUNT_KEEP_HIT_ACTIVE  = {'days' : 30, 'minutes' : 30}

        Accepts days, seconds, microseconds, milliseconds, minutes,
        hours, and weeks.  It's creating a datetime.timedelta object.

        """
        grace = getattr(settings, "HITCOUNT_KEEP_HIT_ACTIVE", {"days": 7})
        period = timezone.now() - timedelta(**grace)
        return self.filter(created__gte=period).filter(*args, **kwargs)
