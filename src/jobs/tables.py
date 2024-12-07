"""This module defines the table used to show jobs."""

import django_tables2 as tables
from django.utils.safestring import mark_safe

from utils.filters import filter_button
from utils.tables import LocalTimeColumn

from .models import BaseJob


class JobTable(tables.Table):
    """Defines the django-tables2 used to show jobs."""

    uuid = tables.Column(verbose_name="Job UUID")
    basefile = tables.Column(verbose_name="File", linkify=True)
    job_type = tables.Column(verbose_name="Job Type")
    user = tables.Column(linkify=True)
    result_url = tables.Column(verbose_name="Result url")
    created_at = LocalTimeColumn()
    updated_at = LocalTimeColumn()

    class Meta:
        """Define model, template, fields."""

        model = BaseJob
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "uuid",
            "basefile",
            "job_type",
            "width",
            "height",
            "filetype",
            "custom_aspect_ratio",
            "source_url",
            "result_url",
            "user",
            "client_uuid",
            "client_version",
            "finished",
            "created_at",
            "updated_at",
        )

    def render_basefile(self, record: BaseJob) -> str:
        """Render the basefile column with a filter button."""
        return filter_button(
            text=f'<a href="{record.basefile.get_absolute_url()}">{record.basefile.title}</a>',
            request=self.request,
            files=record.basefile.uuid,
        )

    def render_job_type(self, record: BaseJob) -> str:
        """Render the jobtype column with a filter button."""
        return filter_button(text=record.job_type, request=self.request, job_types=record.job_type.lower())

    def render_user(self, record: BaseJob) -> str:
        """Render the user column with a filter button."""
        if record.user:
            return filter_button(
                text=f'<a href="{record.user.get_absolute_url()}">{record.user}</a>',
                request=self.request,
                users=record.user.uuid,
            )
        return ""

    def render_client_uuid(self, record: BaseJob) -> str:
        """Render the client_uuid column with a filter button."""
        return filter_button(text=record.client_uuid, request=self.request, client_uuid=record.client_uuid)

    def render_client_version(self, record: BaseJob) -> str:
        """Render the client_version column with a filter button."""
        return filter_button(text=record.client_version, request=self.request, client_version=record.client_version)

    def render_source_url(self, record: BaseJob) -> str:
        """Render the source url column with a filter button."""
        return filter_button(
            text=f'<a href="{record.source_url}">Source</a>',
            request=self.request,
            source_url__icontains=record.source_url,
        )

    def render_result_url(self, record: BaseJob, value: str) -> str:
        """Render the result url column."""
        return mark_safe(f'<a href="{value}">Result</a>')  # noqa: S308
