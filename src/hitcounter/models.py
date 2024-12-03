"""Models for the hitcounter.

Originally based on https://github.com/thornomad/django-hitcount/
"""

from django.conf import settings
from django.db import models
from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _

from .managers import HitManager

delete_hit_count = Signal()
AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")


class BaseHit(models.Model):
    """Abstract model, captures a single Hit by a visitor.

    None of the fields are editable because they are all dynamically created.
    Browsing the Hit list in the Admin will allow one to blocklist both
    IP addresses as well as User Agents. Blocklisting simply causes those
    hits to not be counted or recorded.

    Depending on how long you set the HITCOUNT_KEEP_HIT_ACTIVE, and how long
    you want to be able to use `HitCount.hits_in_last(days=30)` you can choose
    to clean up your Hit table by using the management `hitcount_cleanup`
    management command.
    """

    created_at = models.DateTimeField(editable=False, auto_now_add=True, db_index=True)
    ip = models.CharField(max_length=40, editable=False, db_index=True)
    session = models.CharField(max_length=40, editable=False, db_index=True)
    user_agent = models.CharField(max_length=255, editable=False)
    user = models.ForeignKey(AUTH_USER_MODEL, null=True, editable=False, on_delete=models.CASCADE)

    objects = HitManager()

    class Meta:
        """Meta options for the Hit model."""

        abstract = True
        ordering = ("-created_at",)
        get_latest_by = "created_at"
        verbose_name = _("hit")
        verbose_name_plural = _("hits")

    def __str__(self) -> str:
        """A string representation."""
        return f"Hit: {self.pk}"


class BlocklistIP(models.Model):
    """Model to contain ignored IP addresses."""

    ip = models.CharField(max_length=40, unique=True)

    class Meta:
        """Meta options for the BlocklistIP model."""

        db_table = "hitcount_blocklist_ip"
        verbose_name = _("Blocklisted IP")
        verbose_name_plural = _("Blocklisted IPs")

    def __str__(self) -> str:
        """A string representation."""
        return self.ip


class BlocklistUserAgent(models.Model):
    """Model to contain ignored useragents."""

    user_agent = models.CharField(max_length=255, unique=True)

    class Meta:
        """Meta options for the BlocklistUserAgent model."""

        db_table = "hitcount_blocklist_user_agent"
        verbose_name = _("Blocklisted User Agent")
        verbose_name_plural = _("Blocklisted User Agents")

    def __str__(self) -> str:
        """A string representation."""
        return self.user_agent


class FileHit(BaseHit):
    """Contains BaseFile Hits."""

    content_object = models.ForeignKey(
        "files.BaseFile",
        on_delete=models.CASCADE,
        related_name="hits",
    )


class AlbumHit(BaseHit):
    """Contains Album Hits."""

    content_object = models.ForeignKey(
        "albums.Album",
        on_delete=models.CASCADE,
        related_name="hits",
    )


class TagHit(BaseHit):
    """Contains Tag Hits."""

    content_object = models.ForeignKey(
        "tags.BmaTag",
        on_delete=models.CASCADE,
        related_name="hits",
    )
