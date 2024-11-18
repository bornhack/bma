"""This module defines the table used to show files."""

import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import BaseFile


class FileTable(tables.Table):
    """Defines the django-tables2 used to show files."""

    selection = tables.CheckBoxColumn(accessor="pk", orderable=False)
    uuid = tables.Column(linkify=True, verbose_name="File UUID")
    thumbnail = tables.TemplateColumn(
        verbose_name="Thumbnail",
        template_name="includes/file_thumbnail.html",
        extra_context={"width": 100, "ratio": "16/9"},
    )
    albums = tables.Column(verbose_name="Albums")
    uploader = tables.Column(linkify=True)
    hitcount = tables.Column(verbose_name="Hits")
    jobs = tables.Column(verbose_name="Jobs")
    file_type = tables.Column(verbose_name="File Type")

    def render_albums(self, record: BaseFile) -> str:
        """Render albums as a list of links."""
        output = ""
        for album in record.active_albums_list:
            url = reverse("albums:album_table", kwargs={"album_uuid": album.pk})
            output += f'<a href="{url}">{album.title}&nbsp;({len(album.active_files_list)})</a><br>'
        if not output:
            output = "N/A"
        return mark_safe(output)  # noqa: S308

    def render_tags(self, record: BaseFile) -> str:
        """Render tags in a taggy way."""
        output = ""
        for tag in record.tag_list:
            output += f'<span class="badge bg-secondary">{tag}</span> '
        if not output:
            output = "N/A"
        return mark_safe(output)  # noqa: S308

    def render_jobs(self, record: BaseFile) -> str:
        """Render the jobs column."""
        finished_url = reverse("jobs:job_list") + f"?files={record.uuid}&finished=true"
        unfinished_url = reverse("jobs:job_list") + f"?files={record.uuid}&finished=false"
        return mark_safe(  # noqa: S308
            f'<a href="{unfinished_url}">{record.jobs_unfinished}</a> / '
            f'<a href="{finished_url}">{record.jobs_finished}</a>'
        )

    def render_file_size(self, value: int) -> str:
        """Render the file size column."""
        return f"{intcomma(value)} bytes"

    def render_file_type(self, record: BaseFile) -> str:
        """Render the filetype column."""
        return mark_safe(f'<i class="{record.filetype_icon} fa-2x"></i>')  # noqa: S308

    class Meta:
        """Define model, template, fields."""

        model = BaseFile
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "selection",
            "uuid",
            "thumbnail",
            "title",
            "albums",
            "attribution",
            "uploader",
            "license",
            "file_size",
            "file_type",
            "tags",
            "hitcount",
            "jobs",
            "approved",
            "published",
            "deleted",
        )
