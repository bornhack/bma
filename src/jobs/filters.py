"""Filters used in django-ninja jobs endpoints."""

import uuid
from typing import TYPE_CHECKING
from typing import ClassVar

import django_filters

from files.models import BaseFile
from jobs.models import BaseJob
from users.models import User
from utils.api import CommaStrToUuidList
from utils.filters import ListFilters

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest


class JobFilters(ListFilters):
    """Ninja filters for the job_list API endpoint."""

    file_uuid: uuid.UUID | None = None
    user_uuid: uuid.UUID | None = None
    client_uuid: uuid.UUID | None = None
    client_version: str | None = None
    finished: bool | None = None
    skip_jobs: CommaStrToUuidList | None = None


def get_user_widget_data(request: "HttpRequest") -> "QuerySet[User]":
    """Use handle and display name in the widget."""
    return User.objects.filter(assigned_jobs__isnull=False).distinct()


def get_permitted_files(request: "HttpRequest") -> "QuerySet[BaseFile]":
    """Called by JobFilter to get files for the form field."""
    return BaseFile.bmanager.get_permitted(user=request.user).all()  # type: ignore[no-any-return]


class JobFilter(django_filters.FilterSet):
    """The Job filter used by django-filters."""

    # when filtering by files only show files the user has permission for in the form
    files = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="files",
        queryset=get_permitted_files,
        method="filter_files",
        label="Job related to files",
    )

    users = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="user__handle",
        queryset=get_user_widget_data,
        method="filter_users",
        label="Jobs assigned to users",
    )

    job_types = django_filters.filters.MultipleChoiceFilter(
        choices=(
            ("imageconversionjob", "ImageConversionJob"),
            ("imageexifextractionjob", "ImageExifExtractionJob"),
            ("thumbnailsourcejob", "ThumbnailSourceJob"),
            ("thumbnailjob", "ThumbnailJob"),
        ),
        method="filter_job_types",
        label="Job of these types",
    )

    finished = django_filters.filters.BooleanFilter()

    def filter_files(self, queryset: "QuerySet[BaseJob]", name: str, value: str) -> "QuerySet[BaseJob]":
        """Only show jobs for these files."""
        if not value:
            return queryset
        return queryset.filter(basefile__in=value)

    def filter_users(self, queryset: "QuerySet[BaseJob]", name: str, value: str) -> "QuerySet[BaseJob]":
        """Include only jobs assigned to one of the selected users."""
        if not value:
            return queryset
        return queryset.filter(user__handle__in=value)

    def filter_job_types(self, queryset: "QuerySet[BaseJob]", name: str, value: str) -> "QuerySet[BaseJob]":
        """Include only jobs of certain types."""
        return queryset.filter(polymorphic_ctype__model__in=value)

    class Meta:
        """Set model and fields."""

        model = BaseJob
        fields: ClassVar[dict[str, list[str]]] = {
            "client_uuid": ["exact"],
            "client_version": ["icontains"],
        }
