"""BMA URL Configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", TemplateView.as_view(template_name="frontpage.html"), name="frontpage"),
    path("galleries/", include("galleries.urls", namespace="galleries")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
