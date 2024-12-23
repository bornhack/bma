"""Permissions table."""

from typing import TYPE_CHECKING

import django_tables2 as tables
from django.utils.safestring import mark_safe

from utils.templatetags.bma_utils import get_group_icons

if TYPE_CHECKING:
    from .models import Permission


class PermissionTable(tables.Table):
    """Define the table to show user and group permissions for files and albums."""

    entity = tables.Column(verbose_name="Entity", empty_values=())
    entity_type = tables.Column(verbose_name="Type", empty_values=())
    permission__name = tables.Column(verbose_name="Permission")
    permission__codename = tables.Column()
    created_at = tables.Column()
    created_by = tables.Column()

    class Meta:
        """Define template."""

        template_name = "django_tables2/bootstrap5.html"

    def render_entity_type(self, record: "Permission") -> str:
        """Return type (user or group)."""
        return "user" if hasattr(record, "user") else "group"

    def render_entity(self, record: "Permission") -> str:
        """Return user or group."""
        if hasattr(record, "user"):
            icons = get_group_icons(user=record.user)
            entity = f'<a href="{record.user.get_absolute_url()}">{record.user.handle}</a> {icons}'
        else:
            entity = f'{record.group} <i class="fas fa-users"></i>'
        return mark_safe(entity)  # noqa: S308

    def render_created_by(self, record: "Permission") -> str:
        """Render user handle with link."""
        icons = get_group_icons(user=record.created_by)
        user = f'<a href="{record.created_by.get_absolute_url()}">{record.created_by.handle}</a> {icons}'
        return mark_safe(user)  # noqa: S308
