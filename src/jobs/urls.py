"""URLs for the jobs app."""

from django.urls import path

from jobs.views import JobGrindView
from .views import JobListView

app_name = "jobs"

urlpatterns = [
    path("", JobListView.as_view(), name="job_list"),
    path("/grinder", JobGrindView.as_view(), name="job_grinder"),
]
