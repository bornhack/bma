"""Managers for the Album model."""

from typing import Self

from django.db import models
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone

from files.models import BaseFile


class AlbumManager(models.Manager):  # type: ignore[type-arg]
    """This is the default manager for the Album model."""

    def get_queryset(self):  # type: ignore[no-untyped-def]  # noqa: ANN201
        """Annotations and prefetches for the Album model."""
        return super().get_queryset()


class AlbumQuerySet(models.QuerySet):  # type: ignore[type-arg]
    """Custom queryset for album operations."""

    def prefetch_active_files_list(self, *, recursive: bool = True) -> Self:
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

    def prefetch_user_permissions(self) -> Self:
        """Prefetch user permissions."""
        return self.prefetch_related("user_permissions__user").prefetch_related("user_permissions__permission")

    def prefetch_group_permissions(self) -> Self:
        """Prefetch group permissions."""
        return self.prefetch_related("group_permissions__group").prefetch_related("group_permissions__permission")

    def annotate_hitcount(self) -> Self:
        """Annotate hitcounts for the qs."""
        return self.annotate(hitcount=Count("hits", distinct=True))

    def annotate_memberships(self) -> Self:
        """Annotate membership counts."""
        active_memberships = Count("memberships", filter=Q(memberships__period__contains=timezone.now()), distinct=True)
        historic_memberships = Count("memberships", filter=Q(memberships__period__endswith__lt=timezone.now()))
        future_memberships = Count("memberships", filter=Q(memberships__period__startswith__gt=timezone.now()))
        return self.annotate(
            active_memberships=active_memberships,
            historic_memberships=historic_memberships,
            future_memberships=future_memberships,
        )

    def select_owner(self) -> Self:
        """Get owner with select_related()."""
        return self.select_related("owner")
