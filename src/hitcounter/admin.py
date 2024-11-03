"""Admin for the hitcounter.

Most of this code is originally borrowed from https://github.com/thornomad/django-hitcount/
"""

from typing import Any

from django.contrib import admin
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import AlbumHit
from .models import BaseHit
from .models import BlocklistIP
from .models import BlocklistUserAgent
from .models import FileHit
from .models import TagHit


@admin.register(FileHit, AlbumHit, TagHit)
class HitAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """ModelAdmin for the Hit models."""

    list_display = ("id", "content_object", "created", "user", "ip", "user_agent")
    search_fields = ("ip", "user_agent")
    date_hierarchy = "created"
    actions = (
        "blocklist_ips",
        "blocklist_user_agents",
        "blocklist_delete_ips",
        "blocklist_delete_user_agents",
    )

    def __init__(self, *args: Any, **kwargs: dict[str, str]) -> None:  # noqa: ANN401
        """Disable list_display_links."""
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.list_display_links = None

    def has_add_permission(self, request: HttpRequest) -> bool:
        """No adding."""
        return False

    @admin.action(description=_("Blocklist selected IP addresses"))
    def blocklist_ips(self, request: HttpRequest, queryset: models.QuerySet[BaseHit]) -> None:
        """Add blocklist IP entries."""
        for obj in queryset:
            ip, created = BlocklistIP.objects.get_or_create(ip=obj.ip)
            if created:
                ip.save()
        msg = _("Successfully blocklisted %d IPs") % queryset.count()
        self.message_user(request, msg)

    @admin.action(description=_("Blocklist selected User Agents"))
    def blocklist_user_agents(self, request: HttpRequest, queryset: models.QuerySet[BaseHit]) -> None:
        """Add blocklist useragent entries."""
        for obj in queryset:
            ua, created = BlocklistUserAgent.objects.get_or_create(user_agent=obj.user_agent)
            if created:
                ua.save()
        msg = _("Successfully blocklisted %d User Agents") % queryset.count()
        self.message_user(request, msg)

    @admin.action(description=_("Delete selected hits and blocklist related IP addresses"))
    def blocklist_delete_ips(self, request: HttpRequest, queryset: models.QuerySet[BaseHit]) -> None:
        """Blocklist IP entries and remove Hits."""
        self.blocklist_ips(request, queryset)
        self.delete_queryset(request, queryset)

    @admin.action(description=_("Delete selected hits and blocklist related User Agents"))
    def blocklist_delete_user_agents(self, request: HttpRequest, queryset: models.QuerySet[BaseHit]) -> None:
        """Blocklist useragent entries and delete Hits."""
        self.blocklist_user_agents(request, queryset)
        self.delete_queryset(request, queryset)


@admin.register(BlocklistIP)
class BlocklistIPAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """ModelAdmin for the BlocklistIP model."""


@admin.register(BlocklistUserAgent)
class BlocklistUserAgentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """ModelAdmin for the BlocklistUserAgent model."""
