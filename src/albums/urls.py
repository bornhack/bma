"""URLs for the albums app."""

from django.urls import include
from django.urls import path
from django.views.generic import RedirectView

from .views import AlbumAddFilesView
from .views import AlbumCreateView
from .views import AlbumDetailView
from .views import AlbumListView
from .views import AlbumRemoveFilesView
from .views import AlbumUpdateView

app_name = "albums"

urlpatterns = [
    path("", AlbumListView.as_view(), name="album_list"),
    path("create/", AlbumCreateView.as_view(), name="album_create"),
    path("add-files-to-album/", AlbumAddFilesView.as_view(), name="add_files_to_album"),
    path("remove-files-from-album/", AlbumRemoveFilesView.as_view(), name="remove_files_from_album"),
    path(
        "<uuid:album_uuid>/",
        include(
            [
                path("", RedirectView.as_view(pattern_name="albums:album_slideshow"), name="album_detail"),
                path("update/", AlbumUpdateView.as_view(), name="album_update"),
                path("slideshow/", AlbumDetailView.as_view(), name="album_slideshow"),
                path("table/", AlbumDetailView.as_view(), name="album_table"),
                path("add-files/", AlbumAddFilesView.as_view(), name="album_add_files"),
                path("remove-files/", AlbumRemoveFilesView.as_view(), name="album_remove_files"),
            ]
        ),
    ),
]
