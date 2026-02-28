"""Custom model manager and queryset for the Job polymorphic model."""

from typing import TYPE_CHECKING

from django.db import models

from utils.polymorphic_related import RelatedPolymorphicManager

if TYPE_CHECKING:
    from .models import BaseJob


class JobManager(RelatedPolymorphicManager):
    """Custom manager for job operations."""

    def get_queryset(self) -> models.QuerySet["BaseJob"]:  # type: ignore[override]
        """Prefetch and annotate."""
        from jobs.models import ImageConversionJob  # noqa: PLC0415
        from jobs.models import ThumbnailJob  # noqa: PLC0415
        from jobs.models import ThumbnailSourceJob  # noqa: PLC0415

        return (  # type: ignore[no-any-return]
            super()  # type: ignore[attr-defined]
            .get_queryset()
            .select_related("basefile")
            .select_related("user")
            # get fields for models inheriting from Job
            .select_polymorphic_related(ImageConversionJob, "imageversion")
            .select_polymorphic_related(ThumbnailJob, "thumbnail")
            .select_polymorphic_related(ThumbnailSourceJob, "thumbnailsource")
        )
