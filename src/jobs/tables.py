"""This module defines the table used to show jobs."""

import django_tables2 as tables
from django.utils.safestring import mark_safe

from utils.filters import filter_button
from utils.tables import BPBooleanColumn
from utils.tables import BPColumn
from utils.tables import BPLocalTimeColumn
from utils.tables import BPOverflowColumn

from .models import BaseJob


class JobTable(tables.Table):
    """Defines the django-tables2 used to show jobs."""

    uuid = BPOverflowColumn(bp="lg", verbose_name="Job UUID")
    basefile = tables.Column(verbose_name="File", linkify=True)
    job_type = tables.Column(verbose_name="Job Type")
    result_url = tables.Column(verbose_name="Result url")

    # show only at xxl and up
    width = BPColumn(bp="xxl")
    height = BPColumn(bp="xxl")
    filetype = BPColumn(bp="xxl")
    custom_aspect_ratio = BPColumn(bp="xxl", verbose_name="Custom AR")
    source_url = BPColumn(bp="xxl")

    # show only at 3xl and up
    finished = BPBooleanColumn(bp="3xl")

    # show only at 4xl and up
    user = BPColumn(bp="4xl", linkify=True)

    # show only at 5xl and up
    client_uuid = BPColumn(bp="5xl")
    client_version = BPOverflowColumn(bp="5xl")
    created_at = BPLocalTimeColumn(bp="5xl")
    updated_at = BPLocalTimeColumn(bp="5xl")

    class Meta:
        """Define model, template, fields."""

        model = BaseJob
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            "uuid",
            "basefile",
            "job_type",
            "result_url",
            # xxl
            "width",
            "height",
            "filetype",
            "custom_aspect_ratio",
            # 3xl
            "source_url",
            "finished",
            # 4xl
            "user",
            "client_uuid",
            "client_version",
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
