"""CBV mixins for file based views."""

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.views.generic.detail import SingleObjectMixin

from .models import BaseFile


class FileViewMixin(SingleObjectMixin[BaseFile]):
    """A mixin shared by views working on files, sets self.file from file_uuid in url kwargs."""

    def setup(self, request: HttpRequest, *args: str, **kwargs: dict[str, str]) -> None:
        """Get file object from url."""
        super().setup(request, *args, **kwargs)  # type: ignore[misc]
        self.object = self.file = get_object_or_404(
            BaseFile.bmanager.get_permitted(user=self.request.user),  # type: ignore[attr-defined]
            uuid=kwargs["file_uuid"],
        )

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, str]:
        """Add file to context."""
        context = super().get_context_data(**kwargs)
        context["file"] = self.file
        return context
