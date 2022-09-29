"""BMA URL Configuration."""
from django.conf import settings
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views.generic import TemplateView

from .api import api_v1_json
from files.views import BMAMediaView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/v1/json/", api_v1_json.urls),
    path("", TemplateView.as_view(template_name="frontpage.html"), name="frontpage"),
    path("files/", include("files.urls", namespace="files")),
    path("pictures/", include("pictures.urls", namespace="pictures")),
    path("videos/", include("videos.urls", namespace="videos")),
    path("audios/", include("audios.urls", namespace="audios")),
    path("documents/", include("documents.urls", namespace="documents")),
]

# we are serving media files through nginx using X-Accel-Redirect in prod,
# and locally during development, determined by the value of 'accel' arg to BMAMediaView
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)",
        BMAMediaView,
        name="nginx_accel_media",
        kwargs={"accel": settings.NGINX_PROXY},
    ),
]
