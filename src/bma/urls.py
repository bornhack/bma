"""BMA URL Configuration."""

from django.conf import settings
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.urls import re_path

from bma.api import api_v1_json
from files.views import bma_media_view
from users.views import UserSettingsUpdateView
from users.views import UserSettingsView
from utils.admin import file_admin
from utils.views import csrfview

from .oauth2_urls import oauth2_endpoint_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("manage/", file_admin.urls),
    path("accounts/", include("allauth.urls")),
    path("api/v1/json/", api_v1_json.urls),
    path("api/csrf/", csrfview),
    path("o/", include((oauth2_endpoint_views, "oauth2_provider"), namespace="oauth2_provider")),
    path("", include("frontpage.urls")),
    path("files/", include("files.urls", namespace="files")),
    path("albums/", include("albums.urls", namespace="albums")),
    path("widgets/", include("widgets.urls", namespace="widgets")),
    path("users/", include("users.urls", namespace="users")),
    path("jobs/", include("jobs.urls", namespace="jobs")),
    path("settings/", UserSettingsView.as_view(), name="user_settings"),
    path("settings/update/", UserSettingsUpdateView.as_view(), name="user_settings_update"),
    # BMA serves media files through nginx using X-Accel-Redirect in prod,
    # and locally during development, determined by the value of 'accel' arg to bma_media_view
    re_path(
        r"^media/(?P<path>.*)",
        bma_media_view,
        name="bma_media_view",
        kwargs={"accel": settings.NGINX_PROXY},
    ),
]

if settings.DEBUG_TOOLBAR:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
