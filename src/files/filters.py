"""The filters used for the file_list API endpoint and django-filters for regular views."""

import uuid
from typing import ClassVar

import django_filters
from django.db import models
from django.utils import timezone

from albums.models import Album
from files.models import LicenseChoices
from tags.models import BmaTag
from users.models import User
from utils.filters import FileAlbumSortingChoices
from utils.filters import ListFilters

from .models import BaseFile
from .models import FileTypeChoices


class FileFilters(ListFilters):
    """The filters used for the file_list API endpoint."""

    albums: list[uuid.UUID] | None = None
    uploaders: list[uuid.UUID] | None = None
    licenses: list[str] | None = None
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
    sorting: FileAlbumSortingChoices | None = None


# Sorting choices for the web UI FileFilter.
# Uses Django-style ordering strings (prefix with "-" for descending).
SORT_CHOICES = (
    ("-created_at", "Newest first"),
    ("created_at", "Oldest first"),
    ("-updated_at", "Recently updated"),
    ("updated_at", "Least recently updated"),
    ("title", "Title (A-Z)"),
    ("-title", "Title (Z-A)"),
    ("-hitcount", "Most popular"),
    ("hitcount", "Least popular"),
)


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


FILETYPE_CHOICES = (
    ("image", "Image"),
    ("video", "Video"),
    ("audio", "Audio"),
    ("document", "Document"),
)


class FileFilter(django_filters.FilterSet):
    """The main django-filters filter used in views showing files."""

    @property
    def qs(self) -> models.QuerySet[BaseFile]:
        """Apply sorting after filtering, default to newest first."""
        qs = super().qs
        sort = self.data.get("sort") if self.data else None
        if sort:
            if sort in ("-hitcount", "hitcount"):
                qs = qs.annotate(hitcount=models.Count("hits", distinct=True))
            qs = qs.order_by(sort)
        else:
            qs = qs.order_by("-created_at")
        return qs  # type: ignore[no-any-return]

    ####### SORTING ##################
    sort = django_filters.ChoiceFilter(
        choices=SORT_CHOICES,
        label="Sort by",
        method="filter_sort",
    )

    def filter_sort(self, queryset: models.QuerySet[BaseFile], name: str, value: str) -> models.QuerySet[BaseFile]:
        """No-op: actual sorting is applied in the qs property.

        This method exists because django_filters requires a method for
        custom filters, but we handle ordering in the qs property to
        ensure it runs after all other filters.
        """
        return queryset

    ####### FILETYPES ##############
    file_types = django_filters.MultipleChoiceFilter(
        method="file_types_filter", choices=FILETYPE_CHOICES, label="File Types"
    )

    def file_types_filter(
        self, queryset: models.QuerySet[BaseFile], name: str, value: list[str]
    ) -> models.QuerySet[BaseFile]:
        """Filter by filetype/polymorphic subclass."""
        selected_types = [model for model in BaseFile.__subclasses__() if model.__name__.lower() in value]
        return queryset.instance_of(*selected_types)  # type: ignore[no-any-return,attr-defined]

    ####### LICENSES ##############
    licenses = django_filters.MultipleChoiceFilter(
        method="licenses_filter", choices=LicenseChoices, label="Files With Licenses"
    )

    def licenses_filter(
        self, queryset: models.QuerySet[BaseFile], name: str, value: list[str]
    ) -> models.QuerySet[BaseFile]:
        """Filter by license."""
        return queryset.filter(license__in=value)

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
        """Include only files tagged by any of the selected taggers."""
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
        """Set model  and fields."""

        model = BaseFile
        fields: ClassVar[dict[str, list[str]]] = {
            "attribution": ["icontains"],
            "mimetype": ["icontains"],
            "title": ["icontains"],
            "approved": ["exact"],
            "published": ["exact"],
            "deleted": ["exact"],
            "file_size": ["exact", "lt", "gt"],
        }
