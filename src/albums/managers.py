"""Managers for the Album model."""

from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone

from files.models import BaseFile

if TYPE_CHECKING:
    from .models import Album


class AlbumManager(models.Manager):  # type: ignore[type-arg]
    """This is the default manager for the Album model."""

    def get_queryset(self):  # type: ignore[no-untyped-def]  # noqa: ANN201
        """Annotations and prefetches for the Album model."""
        qs = super().get_queryset()

        # queries to count past, present, and future memberships of each album
        active_memberships = Count("memberships", filter=Q(memberships__period__contains=timezone.now()), distinct=True)
        historic_memberships = Count("memberships", filter=Q(memberships__period__endswith__lt=timezone.now()))
        future_memberships = Count("memberships", filter=Q(memberships__period__startswith__gt=timezone.now()))

        return (
            qs.annotate(
                active_memberships=active_memberships,
                historic_memberships=historic_memberships,
                future_memberships=future_memberships,
            )
            .select_related("owner")
            .prefetch_related("user_permissions__user")
            .prefetch_related("user_permissions__permission")
            .prefetch_related("group_permissions__group")
            .prefetch_related("group_permissions__permission")
            .prefetch_related("hits")
            .annotate(hitcount=Count("hits", distinct=True))
            .prefetch_active_files_list(recursive=True)
        )


class AlbumQuerySet(models.QuerySet):  # type: ignore[type-arg]
    """Custom queryset for album operations."""

    def prefetch_active_files_list(self, *, recursive: bool = True) -> models.QuerySet["Album"]:
        """Prefetch active files for each Album into a list.

        Do NOT use the BaseFile bmanager when prefetching inside the Album bmanager,
        confusion, sorrow, anger and hatred lies down that path.

        If recursive is True then each prefetched file also gets a prefetch list of active albums.
        """
        if recursive:
            qs = (
                BaseFile.objects.filter(
                    memberships__period__contains=timezone.now(),
                )
                .distinct()
                # prefetch active albums for each prefetched file
                .prefetch_active_albums_list(recursive=False)
            )
        else:
            # do not prefetch active albums for each file
            qs = BaseFile.objects.filter(
                memberships__period__contains=timezone.now(),
            ).distinct()

        return self.prefetch_related(
            models.Prefetch(
                "files",
                queryset=qs,
                to_attr="active_files_list",
            ),
        )
