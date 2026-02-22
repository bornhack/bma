"""Custom model manager and queryset for the BaseFile model."""

from typing import Self

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import Count
from django.utils import timezone
from guardian.shortcuts import get_objects_for_user

from users.models import UserType
from utils.polymorphic_related import RelatedPolymorphicManager
from utils.polymorphic_related import RelatedPolymorphicQuerySet


class BaseFileManager(RelatedPolymorphicManager):
    """Custom manager for file operations."""


class BaseFileQuerySet(RelatedPolymorphicQuerySet):
    """Custom queryset for bmanager file operations."""

    def prefetch_image_version_list(self) -> Self:
        """Prefetch image version list."""
        return self.prefetch_related(models.Prefetch("image_versions", to_attr="image_version_list"))

    def prefetch_thumbnail_list(self) -> Self:
        """Prefetch thumbnail list."""
        return self.prefetch_related(models.Prefetch("thumbnails", to_attr="thumbnail_list"))

    def prefetch_tag_list(self) -> Self:
        """Prefetch tag list."""
        return self.prefetch_related(models.Prefetch("tags", to_attr="tag_list"))

    def prefetch_thumbnails(self) -> Self:
        """Prefetch thumbnails."""
        return self.prefetch_related("thumbnails")

    def prefetch_permissions(self) -> Self:
        """Prefetch user and group permissions for the qs."""
        return (
            self.prefetch_related("user_permissions__user")
            .prefetch_related("user_permissions__permission")
            .prefetch_related("group_permissions__group")
            .prefetch_related("group_permissions__permission")
        )

    def annotate_hitcount(self) -> Self:
        """Annotate hitcounts for the qs."""
        return self.annotate(hitcount=Count("hits", distinct=True))

    def annotate_job_counts(self) -> Self:
        """Annotate jobs_finished and jobs_unfinished on the qs."""
        return self.annotate(jobs_finished=Count("jobs", filter=models.Q(jobs__finished=True))).annotate(
            jobs_unfinished=Count("jobs", filter=models.Q(jobs__finished=False))
        )

    def annotate_permissions(self) -> Self:
        """Annotate permission counts on the qs."""
        return self.annotate(user_permission_count=Count("user_permissions")).annotate(
            group_permission_count=Count("group_permissions")
        )

    def get_for_api_response(self) -> Self:
        """Annotate everything needed for an API response."""
        return self.annotate_job_counts().prefetch_image_version_list()

    def get_permitted(self, user: UserType | AnonymousUser) -> Self:
        """Return files that are approved, published and not deleted, plus files where the user has view_basefile."""
        if hasattr(user, "permitted_files"):
            # not the first call in this request, use cached version
            return user.permitted_files  # type: ignore[no-any-return]
        public_files = self.filter(approved=True, published=True, deleted=False).prefetch_related("uploader")
        perm_files = get_objects_for_user(
            user=user,
            perms="files.view_basefile",
            klass=self.all(),
        ).prefetch_related("uploader")
        files = public_files | perm_files
        # do not return duplicates and cache result
        user.permitted_files = files.distinct()  # type: ignore[union-attr]
        return user.permitted_files  # type: ignore[no-any-return,union-attr]

    def change_bool(self, *, field: str, value: bool) -> int:
        """Change a bool field on a queryset of files."""
        kwargs = {field: value, "updated_at": timezone.now()}
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

    def unsoftdelete(self) -> int:
        """Undelete files in queryset."""
        return self.change_bool(field="deleted", value=False)

    def prefetch_active_albums_list(self, *, recursive: bool = True) -> Self:
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

        return self.prefetch_related(
            models.Prefetch(
                "albums",
                queryset=qs,
                to_attr="active_albums_list",
            )
        )
