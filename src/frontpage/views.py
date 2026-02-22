"""The frontpage view."""

import logging
from typing import Any

from django.db.models import QuerySet
from django.views.generic import TemplateView

from audios.models import Audio
from documents.models import Document
from files.models import BaseFile
from images.models import Image
from videos.models import Video

logger = logging.getLogger("bma")


class FrontpageTemplateView(TemplateView):
    """The frontpage view."""

    template_name = "frontpage.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, QuerySet[Image]]:  # noqa: ANN401
        """Add recent files to the context."""
        context = super().get_context_data(**kwargs)
        context["latest_images"] = self._query_latest_uploads("image")
        context["latest_videos"] = self._query_latest_uploads("video")
        context["latest_audios"] = self._query_latest_uploads("audio")
        context["latest_documents"] = self._query_latest_uploads("document")
        context["popular_images"] = self._query_most_popular("image")
        context["popular_videos"] = self._query_most_popular("video")
        context["popular_audios"] = self._query_most_popular("audio")
        context["popular_documents"] = self._query_most_popular("document")
        return context

    def _query_latest_uploads(self, model: str) -> QuerySet[Audio | Video | Image | Document] | None:
        """Get the latest 12 published uploads for a model."""
        qs = (
            BaseFile.bmanager.get_permitted(user=self.request.user)
            .filter(polymorphic_ctype__model=model)
            .prefetch_thumbnail_list()
            .order_by("-created_at")
        )
        if model == "image":
            qs = qs.prefetch_image_version_list()
        return qs[:12]

    def _query_most_popular(self, model: str) -> QuerySet[Audio | Video | Image | Document] | None:
        """Get the 12 most popular uploads for a model."""
        qs = (
            BaseFile.bmanager.get_permitted(user=self.request.user)
            .filter(polymorphic_ctype__model=model)
            .prefetch_thumbnail_list()
            .annotate_hitcount()
            .order_by("-hitcount")
        )
        if model == "image":
            qs = qs.prefetch_image_version_list()
        return qs[:12]
