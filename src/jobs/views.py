"""Job related views."""

from typing import TYPE_CHECKING

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from files.models import BaseFile

from .filters import JobFilter
from .models import BaseJob
from .tables import JobTable

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.forms import Form


class JobListView(SingleTableMixin, FilterView):
    """Job list view."""

    model = BaseJob
    table_class = JobTable
    template_name = "job_list.html"
    filterset_class = JobFilter
    context_object_name = "jobs"

    def get_queryset(self, queryset: "QuerySet[BaseJob] | None" = None) -> "QuerySet[BaseJob]":
        """Use bmanager to get juicy file objects."""
        return BaseJob.objects.select_related("basefile")  # type: ignore[no-any-return]

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, "Form"]:
        """Add form to the context."""
        context = super().get_context_data(**kwargs)
        context["total_jobs"] = BaseJob.objects.filter(
            basefile__in=BaseFile.bmanager.get_permitted(user=self.request.user)
        ).count()
        return context  # type: ignore[no-any-return]
