"""The filters used for the tag_list API endpoint and django-filters for regular views."""

import uuid
from typing import ClassVar

import django_filters

from utils.filters import ListFilters

from .models import BmaTag


class TagFilters(ListFilters):
    """The filters used for the tag_list API endpoint."""

    name: list[str] | None = None
    taggers: list[uuid.UUID] | None = None


class TagFilter(django_filters.FilterSet):
    """The main django-filters filter used in views showing files."""

    class Meta:
        """Set model and fields."""

        model = BmaTag
        fields: ClassVar[dict[str, list[str]]] = {
            "name": ["contains", "exact"],
        }
