"""This module defines the table used to show files."""

import django_tables2 as tables
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import BaseFile


class FileTable(tables.Table):
    """Defines the django-tables2 used to show files."""

    selection = tables.CheckBoxColumn(accessor="pk", orderable=False)
    uuid = tables.Column(linkify=True)
    albums = tables.Column(verbose_name="Albums")
    uploader = tables.Column(linkify=True)
    hitcount = tables.Column(verbose_name="Hits")
    jobs = tables.Column(verbose_name="Jobs")

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
        return f"{record.jobs.filter(finished=False).count()} / {record.jobs.filter(finished=True).count()}"

    class Meta:
        """Define model, template, fields."""

        model = BaseFile
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "selection",
            "uuid",
            "title",
            "albums",
            "attribution",
            "uploader",
            "license",
            "file_size",
            "tags",
            "hitcount",
            "jobs",
            "approved",
            "published",
            "deleted",
        )
