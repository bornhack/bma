"""Custom model manager and queryset for the BaseFile model."""

from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Count
from django.utils import timezone
from guardian.shortcuts import get_objects_for_user
from polymorphic.managers import PolymorphicManager
from polymorphic.managers import PolymorphicQuerySet

from users.models import UserType

if TYPE_CHECKING:
    from .models import BaseFile


class BaseFileManager(PolymorphicManager):
    """Custom manager for file operations."""

    def get_queryset(self) -> models.QuerySet["BaseFile"]:
        """Prefetch active albums into a list."""
        return (  # type: ignore[no-any-return]
            super()
            .get_queryset()
            .prefetch_related("user_permissions__user")
            .prefetch_related("user_permissions__permission")
            .prefetch_related("group_permissions__group")
            .prefetch_related("group_permissions__permission")
            .prefetch_related(
                models.Prefetch("tags", to_attr="tag_list"),
            )
            .prefetch_related("hits")
            .annotate(hitcount=Count("hits", distinct=True))
            .annotate(jobs_finished=Count("jobs", filter=models.Q(jobs__finished=True)))
            .annotate(jobs_unfinished=Count("jobs", filter=models.Q(jobs__finished=False)))
            .prefetch_active_albums_list(recursive=True)
            .prefetch_related("thumbnail")
        )


class BaseFileQuerySet(PolymorphicQuerySet):
    """Custom queryset for bmanager file operations."""

    def get_permitted(self, user: UserType) -> models.QuerySet["BaseFile"]:
        """Return files that are approved, published and not deleted, plus files where the user has view_basefile."""
        public_files = self.filter(approved=True, published=True).prefetch_related("uploader")
        perm_files = get_objects_for_user(
            user=user,
            perms="files.view_basefile",
            klass=self.all(),
        ).prefetch_related("uploader")
        files = public_files | perm_files
        # do not return duplicates
        return files.distinct()  # type: ignore[no-any-return]

    def change_bool(self, *, field: str, value: bool) -> int:
        """Change a bool field on a queryset of files."""
        kwargs = {field: value, "updated": timezone.now()}
        self.update(**kwargs)
        return int(self.count())

    def approve(self) -> int:
        """Approve files in queryset."""
        return self.change_bool(field="approved", value=True)

    def unapprove(self) -> int:
        """Unapprove files in queryset."""
        return self.change_bool(field="approved", value=False)

    def publish(self) -> int:
        """Publish files in queryset."""
        return self.change_bool(field="published", value=True)

    def unpublish(self) -> int:
        """Unpublish files in queryset."""
        return self.change_bool(field="published", value=False)

    def softdelete(self) -> int:
        """Soft-delete files in queryset."""
        return self.change_bool(field="deleted", value=True)

    def undelete(self) -> int:
        """Undelete files in queryset."""
        return self.change_bool(field="deleted", value=False)

    def prefetch_active_albums_list(self, *, recursive: bool = True) -> models.QuerySet["BaseFile"]:
        """Prefetch active albums into a list.

        Do NOT use the Album bmanager when prefetching inside the BaseFile bmanager,
        confusion, sorrow, anger and hatred lies down that path.

        If recursive is True then each prefetched album also gets a prefetch list of active files.
        """
        # late import to avoid circular import
        from albums.models import Album

        if recursive:
            qs = (
                Album.objects.filter(
                    memberships__period__contains=timezone.now(),
                )
                .distinct()
                # prefetch active files for each prefetched album
                .prefetch_active_files_list(recursive=False)
            )
        else:
            # do not prefetch active albums for each prefetched file
            qs = Album.objects.filter(
                memberships__period__contains=timezone.now(),
            ).distinct()

        return self.prefetch_related(  # type: ignore[no-any-return]
            models.Prefetch(
                "albums",
                queryset=qs,
                to_attr="active_albums_list",
            )
        )
