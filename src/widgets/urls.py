"""URLs for the widgets app."""

from django.urls import path

from .views import bma_widget

app_name = "widgets"

urlpatterns = [
    path("<str:style>/<int:count>/<uuid:uuid>/", bma_widget),
]
