"""CBV mixins for tag related views."""

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from files.mixins import FileViewMixin


class TagViewMixin(FileViewMixin):
    """A mixin shared by views working on tags, sets self.tag from tag_name in url kwargs."""

    def setup(self, request: HttpRequest, *args: str, **kwargs: dict[str, str]) -> None:
        """Get tag object from url. Requires self.file to be set."""
        super().setup(request, *args, **kwargs)
        self.tag = get_object_or_404(self.file.tags.all(), slug=kwargs["tag_slug"])

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, str]:
        """Add tag to context."""
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        return context
