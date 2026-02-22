"""CBV mixins for file based views."""

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.http import HttpRequest
from django.views.generic.detail import SingleObjectMixin

from .models import BaseFile


class FileViewMixin(SingleObjectMixin[BaseFile]):
    """A mixin shared by views working on files, sets self.file from file_uuid in url kwargs."""

    def setup(self, request: HttpRequest, *args: str, **kwargs: dict[str, str]) -> None:
        """Get file object from url."""
        super().setup(request, *args, **kwargs)  # type: ignore[misc]
        try:
            self.object = self.file = (
                BaseFile.objects.get_permitted(user=self.request.user)  # type: ignore[attr-defined]
                .prefetch_image_version_list()
                .get(uuid=kwargs["file_uuid"])
            )
        except BaseFile.DoesNotExist as e:
            raise Http404 from e

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, str]:
        """Add file to context."""
        context = super().get_context_data(**kwargs)
        context["file"] = self.file
        return context


class FileChangeViewMixin(SingleObjectMixin[BaseFile]):
    """A mixin shared by views working on files, sets self.file from file_uuid in url kwargs."""

    def setup(self, request: HttpRequest, *args: str, **kwargs: dict[str, str]) -> None:
        """Get file object from url."""
        super().setup(request, *args, **kwargs)  # type: ignore[misc]
        try:
            self.object = self.file = (
                BaseFile.objects.get_permitted(user=self.request.user)  # type: ignore[attr-defined]
                .prefetch_image_version_list()
                .get(uuid=kwargs["file_uuid"])
            )
        except BaseFile.DoesNotExist as e:
            raise Http404 from e

        if not request.user.has_perm("change_basefile", self.file):
            raise PermissionDenied

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, str]:
        """Add file to context."""
        context = super().get_context_data(**kwargs)
        context["file"] = self.file
        return context
