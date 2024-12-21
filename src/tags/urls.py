"""URLs for the tags app."""

from django.urls import path

from .views import TagListView

app_name = "tags"

urlpatterns = [
    path("", TagListView.as_view(), name="tag_list"),
]
