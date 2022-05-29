"""BMA URL Configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views.generic import TemplateView

from utils.views import AccelMediaView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", TemplateView.as_view(template_name="frontpage.html"), name="frontpage"),
    path("galleries/", include("galleries.urls", namespace="galleries")),
]

# are we serving media files through nginx or is this local dev?
if settings.NGINX_PROXY:
    urlpatterns += re_path(
        r"^media/(?P<path>.*)",
        AccelMediaView,
        name="nginx_accel_media",
    )
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
