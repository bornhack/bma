"""This module defines the table used to show albums."""

import django_tables2 as tables

from .models import Album


class AlbumTable(tables.Table):
    """Defines the django-tables2 used to show albums."""

    uuid = tables.Column(linkify=("albums:album_table", {"album_uuid": tables.A("pk")}))
    owner = tables.Column(linkify=True)
    hitcount = tables.Column(verbose_name="Hits")
    active_memberships = tables.Column(verbose_name="Files")

    class Meta:
        """Define model, template, fields."""

        model = Album
        template_name = "django_tables2/bootstrap.html"
        fields = (
            "uuid",
            "title",
            "description",
            "owner",
            "active_memberships",
            "hitcount",
        )
