"""URLs for the jobs app."""

from django.urls import path

from jobs.views import JobGrindView

app_name = "jobs"

urlpatterns = [
    path("", JobGrindView.as_view(), name="grind_list"),
]
