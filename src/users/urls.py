"""URLs for the users app."""

from django.urls import path

from .views import UserProfileView

app_name = "users"

urlpatterns = [
    path("<uuid:user_uuid>/", UserProfileView.as_view(), name="user_profile"),
    path("<slug:user_handle>/", UserProfileView.as_view(), name="user_profile"),
]
