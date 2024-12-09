"""This module defines the table used to show albums."""

import django_tables2 as tables

from .models import Album


class AlbumTable(tables.Table):
    """Defines the django-tables2 used to show albums."""

    uuid = tables.Column(linkify=("albums:album_table", {"album_uuid": tables.A("pk")}))
    title = tables.Column()
    description = tables.Column()
    owner = tables.Column(linkify=True)
    active_memberships = tables.Column(verbose_name="Files")
    hitcount = tables.Column(verbose_name="Hits")

    class Meta:
        """Define model, template, fields."""

        model = Album
        template_name = "django_tables2/bootstrap5.html"
        fields = (
            "uuid",
            "title",
            "description",
            "owner",
            "active_memberships",
            "hitcount",
        )
