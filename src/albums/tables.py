"""This module defines the table used to show albums."""

import django_tables2 as tables

from utils.tables import BPColumn
from utils.tables import OverflowColumn

from .models import Album


class AlbumTable(tables.Table):
    """Defines the django-tables2 used to show albums."""

    uuid = OverflowColumn(linkify=("albums:album_detail_table", {"album_uuid": tables.A("pk")}))
    title = OverflowColumn()
    description = OverflowColumn()
    owner = tables.Column(linkify=True)

    # only shown on xl and up
    active_memberships = BPColumn(bp="xl", verbose_name="Files")
    hitcount = BPColumn(bp="xl", verbose_name="Hits")

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
