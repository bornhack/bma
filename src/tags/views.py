"""Tag related views."""

from typing import TYPE_CHECKING

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .filters import TagFilter
from .models import BmaTag
from .tables import TagTable

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.forms import Form


class TagListView(SingleTableMixin, FilterView):
    """Tag list view."""

    model = BmaTag
    table_class = TagTable
    template_name = "tag_list.html"
    filterset_class = TagFilter
    context_object_name = "tags"

    def get_queryset(self, queryset: "QuerySet[BmaTag] | None" = None) -> "QuerySet[BmaTag]":
        """Get qs with annotations."""
        qs = super().get_queryset()
        return qs.prefetch_related("taggings__tagger")  # type: ignore[no-any-return]

    def get_table_kwargs(self) -> dict[str, tuple[str]]:
        """Exclude weight column, it doesn't make sense in this view."""
        return {"exclude": ("weight",)}

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, "Form"]:
        """Add form to the context."""
        context = super().get_context_data(**kwargs)
        context["total_tags"] = BmaTag.objects.count()
        return context  # type: ignore[no-any-return]
