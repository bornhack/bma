"""Job related views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class JobGrindView(LoginRequiredMixin, TemplateView):
    """The grinder view of many jobs. Uses the API and a js client to grind."""

    template_name = "grinder.html"
