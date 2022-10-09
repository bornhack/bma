from django.urls import path

from albums.views import AlbumListTemplateView

app_name = "albums"

urlpatterns = [
    path("", AlbumListTemplateView.as_view(), name="list"),
]
