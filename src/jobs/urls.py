"""URLs for the jobs app."""

from django.urls import path

from .views import JobListView

app_name = "jobs"

urlpatterns = [
    path("", JobListView.as_view(), name="job_list"),
]
