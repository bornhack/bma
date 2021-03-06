"""URL Configuration for the galleries app."""
from django.urls import include
from django.urls import path

from .views import GalleryCreateView
from .views import GalleryDetailView
from .views import GalleryListView

app_name = "galleries"
urlpatterns = [
    path("", GalleryListView.as_view(), name="gallery_list"),
    path("create/", GalleryCreateView.as_view(), name="gallery_create"),
    path(
        "<slug:slug>/",
        include(
            [
                path("", GalleryDetailView.as_view(), name="gallery_detail"),
            ],
        ),
    ),
]
