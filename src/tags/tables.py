"""This module defines the table used to show tags."""

import django_tables2 as tables
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import BmaTag
from .models import TaggedFile


class TagTable(tables.Table):
    """Defines the django-tables2 used to show tags."""

    def render_name(self, record: BmaTag) -> str:
        """Render tag name as a link to the detail page for the tag on that file."""
        url = reverse(
            "files:file_tag_taggings_list", kwargs={"file_uuid": record.taggedfile_uuid, "tag_slug": record.slug}
        )
        return mark_safe(  # noqa: S308
            f'<a class="link-offset-2 link-offset-3-hover link-underline link-underline-opacity-0 link-underline-opacity-75-hover" href="{url}">{record.name}</a>'  # noqa: E501
        )

    class Meta:
        """Define model, template, fields."""

        model = BmaTag
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "name",
            "weight",
            "created",
            "slug",
        )


class TaggingTable(tables.Table):
    """Defines the django-tables2 used to show taggings."""

    tagger = tables.Column(linkify=True)
    tag__name = tables.Column(verbose_name="Tag")

    class Meta:
        """Define model, template, fields."""

        model = TaggedFile
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "tagger",
            "tag__name",
            "created",
        )
