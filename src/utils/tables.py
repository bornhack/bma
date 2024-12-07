"""Django-tables2 shared stuff."""

from typing import TYPE_CHECKING

import django_tables2 as tables
from django.utils import timezone

if TYPE_CHECKING:
    from datetime import datetime


class LocalTimeColumn(tables.Column):
    """A table column which applies the active timezone."""

    def render(self, value: "datetime") -> "datetime":
        """Apply timezone to the value in the column."""
        return timezone.localtime(value)
