"""This module defines the table used to show files."""

import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils.safestring import mark_safe

from files.models import LicenseChoices
from files.models import license_urls
from utils.filters import filter_button

from .models import BaseFile


class FileTable(tables.Table):
    """Defines the django-tables2 used to show files."""

    selection = tables.CheckBoxColumn(accessor="pk", orderable=False)
    uuid = tables.Column(linkify=True, verbose_name="File UUID")
    thumbnail = tables.TemplateColumn(
        verbose_name="Thumbnail",
        template_name="includes/file_thumbnail_pswp.html",
        extra_context={"width": 100, "ratio": "1/1"},
    )
    albums = tables.Column(verbose_name="Albums")
    uploader = tables.Column(linkify=True)
    hitcount = tables.Column(verbose_name="Hits")
    jobs = tables.Column(verbose_name="Jobs")
    mimetype = tables.Column(verbose_name="File Type")

    def render_title(self, value: str) -> str:
        """Render title with a filter button."""
        return filter_button(text=value, request=self.request, title__icontains=value)

    def render_albums(self, record: BaseFile) -> str:
        """Render albums as a list of links."""
        output = ""
        for album in record.active_albums_list:
            url = reverse("albums:album_table", kwargs={"album_uuid": album.pk})
            output += filter_button(
                text=f'<a href="{url}">{album.title}&nbsp;({len(album.active_files_list)})</a><br>',
                request=self.request,
                in_all_albums=album.uuid,
            )
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

    def render_attribution(self, value: str) -> str:
        """Render the attribution column."""
        return filter_button(text=value, request=self.request, attribution__icontains=value)

    def render_uploader(self, value: str) -> str:
        """Render the uploader column."""
        return filter_button(text=value, request=self.request, uploaders=value)

    def render_file_size(self, value: int) -> str:
        """Render the file size column."""
        return filter_button(text=f"{intcomma(value)} bytes", request=self.request, file_size=str(value))

    def render_mimetype(self, value: str, record: BaseFile) -> str:
        """Render the mimetype column."""
        mimetype = f'<i class="{record.filetype_icon}"></i> {record.filetype}<br>'
        mimetype += filter_button(text=f"<i>{record.mimetype}</i>", request=self.request, mimetype__icontains=value)
        if record.filetype == "image":
            mimetype += f"<br>{record.width}*{record.height}<br>AR {record.aspect_ratio}"
        return mark_safe(mimetype)  # noqa: S308

    def render_license(self, value: str, record: BaseFile) -> str:
        """Render the license column."""
        url = license_urls[record.license]
        title = LicenseChoices[record.license]
        return filter_button(
            text=f'<a title="{title}" href="{url}">{record.license}</a>', request=self.request, license=record.license
        )

    class Meta:
        """Define model, template, fields."""

        model = BaseFile
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "selection",
            "uuid",
            "thumbnail",
            "title",
            "mimetype",
            "file_size",
            "albums",
            "attribution",
            "uploader",
            "license",
            "tags",
            "hitcount",
            "jobs",
            "approved",
            "published",
            "deleted",
        )
