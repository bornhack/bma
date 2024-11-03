"""The filters used for the file_list API endpoint and django-filters for regular views."""

import uuid
from typing import ClassVar

import django_filters
from django.db import models
from django.utils import timezone

from albums.models import Album
from tags.models import BmaTag
from users.models import User
from utils.filters import ListFilters

from .models import BaseFile
from .models import FileTypeChoices
from .models import LicenseChoices


class FileFilters(ListFilters):
    """The filters used for the file_list API endpoint."""

    albums: list[uuid.UUID] | None = None
    uploaders: list[uuid.UUID] | None = None
    licenses: list[LicenseChoices] | None = None
    filetypes: list[FileTypeChoices] | None = None
    approved: bool | None = None
    published: bool | None = None
    deleted: bool | None = None
    size: int | None = None
    size_lt: int | None = None
    size_gt: int | None = None
    attribution: str | None = None
    tags: list[str] | None = None
    taggers: list[uuid.UUID] | None = None


def get_uploader_widget_data() -> list[tuple[str, str]]:
    """Use handle and display name in the widget."""
    return [
        (u[0], f"{u[1]} ({u[0]})")
        for u in User.objects.filter(files__isnull=False).distinct().values_list("handle", "display_name")
    ]


def get_tagged_widget_data() -> list[tuple[str, str]]:
    """Use handle and display name in the widget."""
    return [
        (slug, f"{name} ({slug})")
        for name, slug in BmaTag.objects.filter(taggings__isnull=False)
        .distinct()
        .order_by("slug")
        .values_list("name", "slug")
        if name
    ]


def get_tagger_widget_data() -> list[tuple[str, str]]:
    """Use handle and display name in the widget."""
    return [
        (u[0], f"{u[1]} ({u[0]})")
        for u in User.objects.filter(taggings__isnull=False).distinct().values_list("handle", "display_name")
    ]


class FileFilter(django_filters.FilterSet):
    """The main django-filters filter used in views showing files."""

    @property
    def qs(self) -> models.QuerySet[BaseFile]:
        """This is called after filtering. Make sure only permitted files are returned."""
        queryset = super().qs
        return BaseFile.bmanager.get_permitted(user=self.request.user).filter(  # type: ignore[no-any-return]
            pk__in=queryset.values_list("pk", flat=True)
        )

    ####### ALBUMS #################
    in_all_albums = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="albums",
        queryset=Album.objects.all(),
        method="filter_all_albums",
        label="Files in all albums",
    )

    in_any_albums = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="albums",
        queryset=Album.objects.all(),
        method="filter_any_albums",
        label="Files in any albums",
    )

    not_in_albums = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="albums",
        queryset=Album.objects.all(),
        method="filter_not_albums",
        label="Files not in albums",
    )

    def filter_all_albums(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Include only files with active memberships of all the selected albums."""
        for album in value:
            queryset = queryset.filter(memberships__album__in=[album], memberships__period__contains=timezone.now())
        return queryset

    def filter_any_albums(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Include only files with active memberships of any of the selected albums."""
        if not value:
            return queryset
        # .filter() is OR, use as is
        return queryset.filter(memberships__album__in=value, memberships__period__contains=timezone.now())

    def filter_not_albums(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Include only files without active membership in any of the selected albums."""
        # regular filter OR is fine here
        return queryset.exclude(memberships__album__in=value, memberships__period__contains=timezone.now())

    ####### UPLOADERS #################
    uploaders = django_filters.filters.MultipleChoiceFilter(
        field_name="uploader__handle",
        choices=get_uploader_widget_data,
        method="filter_uploaders",
        label="Files uploaded by",
    )

    not_uploaders = django_filters.filters.MultipleChoiceFilter(
        field_name="uploader__handle",
        choices=get_uploader_widget_data,
        method="filter_not_uploaders",
        label="Files not uploaded by",
    )

    def filter_uploaders(self, queryset: models.QuerySet[BaseFile], name: str, value: str) -> models.QuerySet[BaseFile]:
        """Include only files uploaded by any of the selected uploaders."""
        # we want OR here
        return queryset.filter(uploader__handle__in=value)

    def filter_not_uploaders(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Include only files not uploaded by any of the selected uploaders."""
        # we want OR here
        return queryset.exclude(uploader__handle__in=value)

    ####### TAGS #####################

    tagged_all = django_filters.filters.MultipleChoiceFilter(
        field_name="tags__name",
        choices=get_tagged_widget_data,
        method="filter_tagged_all",
        label="Files tagged with all selected tags",
    )

    tagged_any = django_filters.filters.MultipleChoiceFilter(
        field_name="tags__name",
        choices=get_tagged_widget_data,
        method="filter_tagged_any",
        label="Files tagged with any of the selected tags",
    )

    not_tagged = django_filters.filters.MultipleChoiceFilter(
        field_name="tags__name",
        choices=get_tagged_widget_data,
        method="filter_not_tagged",
        label="Files not tagged with any of the selected tags",
    )

    def filter_tagged_all(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Include only files tagged with all the selected tags."""
        for slug in value:
            queryset = queryset.filter(tags__slug=slug)
        return queryset

    def filter_tagged_any(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Include only files tagged with any of the selected tags."""
        if not value:
            return queryset
        return queryset.filter(tags__slug__in=value)

    def filter_not_tagged(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Exclude files tagged with any of the selected tags."""
        if not value:
            return queryset
        return queryset.exclude(tags__slug__in=value)

    ####### TAGGERS #####################

    taggers_all = django_filters.filters.MultipleChoiceFilter(
        field_name="taggings__tagger__handle",
        choices=get_tagger_widget_data,
        method="filter_taggers_all",
        label="Files tagged by all selected taggers",
    )

    taggers_any = django_filters.filters.MultipleChoiceFilter(
        field_name="taggings__tagger__handle",
        choices=get_tagger_widget_data,
        method="filter_taggers_any",
        label="Files tagged by any of the selected taggers",
    )

    not_taggers = django_filters.filters.MultipleChoiceFilter(
        field_name="taggings__tagger__handle",
        choices=get_tagger_widget_data,
        method="filter_not_taggers",
        label="Files not tagged by any of the selected taggers",
    )

    def filter_taggers_all(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Include only files tagged by all the selected taggers."""
        for handle in value:
            queryset = queryset.filter(taggings__tagger__handle=handle)
        return queryset

    def filter_taggers_any(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Include only files tagged by any of the selected tags."""
        if not value:
            return queryset
        return queryset.filter(taggings__tagger__handle__in=value)

    def filter_not_taggers(
        self, queryset: models.QuerySet[BaseFile], name: str, value: str
    ) -> models.QuerySet[BaseFile]:
        """Exclude files tagged by any of the selected taggers."""
        if not value:
            return queryset
        return queryset.exclude(taggings__tagger__handle__in=value)

    class Meta:
        """Set model and fields."""

        model = BaseFile
        fields: ClassVar[dict[str, list[str]]] = {
            "attribution": ["exact", "icontains"],
            "approved": ["exact"],
            "published": ["exact"],
            "deleted": ["exact"],
            "license": ["exact"],
            "file_size": ["exact", "lt", "gt"],
        }
