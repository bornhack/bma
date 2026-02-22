"""This module defines the table used to show tags."""

import django_tables2 as tables
from django.urls import reverse
from django.utils.safestring import mark_safe

from files.models import BaseFile

from .models import BmaTag
from .models import TaggedFile


class TagTable(tables.Table):
    """Defines the django-tables2 used to show tags.

    This table is used in two contexts. It is used for the tag list
    served at /tags/ and also for the tag list for each file. The columns
    are a bit different but it is basically the same table.
    """

    name = tables.Column(verbose_name="Tag")
    weight = tables.Column(verbose_name="Weight")
    taggings = tables.Column(verbose_name="Taggings")
    tagged_files = tables.Column(verbose_name="Tagged Files", empty_values=(), orderable=False)
    taggings_per_file = tables.Column(verbose_name="Taggings/File", empty_values=(), orderable=False)
    created_at = tables.Column(verbose_name="Tag Time")
    slug = tables.Column(verbose_name="Url Slug")

    class Meta:
        """Define model, template, fields."""

        template_name = "django_tables2/bootstrap5.html"

    def __init__(self, *args: str, basefile: BaseFile | None = None, **kwargs: str) -> None:
        """Save basefile for later."""
        self.basefile = basefile
        super().__init__(*args, **kwargs)

    def render_name(self, record: BmaTag) -> str:
        """Maybe render tag name as a link to the detail page for the tag on that file."""
        if self.basefile:
            url = reverse(
                "files:file_tag_taggings_list", kwargs={"file_uuid": self.basefile.uuid, "tag_slug": record.slug}
            )
            return mark_safe(  # noqa: S308
                f'<a class="link-offset-2 link-offset-3-hover link-underline link-underline-opacity-0 link-underline-opacity-75-hover" href="{url}">{record.name}</a>'  # noqa: E501
            )
        return str(record.name)

    def render_taggings(self, record: BmaTag) -> int:
        """Return the number of taggings with this tag."""
        return int(record.taggings.count())

    def render_tagged_files(self, record: BmaTag) -> str:
        """Return the number of taggings with this tag."""
        url = reverse("files:file_list_table")
        return mark_safe(f'<a href="{url}?tagged_any={record.slug}">{record.tagged_file_count}</a>')  # noqa: S308

    def render_taggings_per_file(self, record: BmaTag) -> float | int:
        """Return the average number of taggings per file with this tag."""
        if record.taggings.count() and record.tagged_file_count:
            return float(record.taggings.count() / record.tagged_file_count)
        return 0


class TaggingTable(tables.Table):
    """Defines the django-tables2 used to show taggings."""

    tagger = tables.Column(linkify=True)
    created_at = tables.Column(verbose_name="Tag Time")

    class Meta:
        """Define model, template, fields."""

        model = TaggedFile
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            "tagger",
            "created_at",
        )
