"""URLs for the widgets app."""

from django.urls import path

from .views import bma_widget_view
from .views import picture_embed_view

app_name = "widgets"

urlpatterns = [
    path("picture/<uuid:image_uuid>/", picture_embed_view, name="picture_embed_view"),
    path("embed/<str:style>/<int:count>/<uuid:uuid>/", bma_widget_view),
]
