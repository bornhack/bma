"""Urls for django-oauth2-toolkit mounted under /o/."""

import oauth2_provider.views as oauth2_views
from oauth2_provider.urls import base_urlpatterns, oidc_urlpatterns
from decorator_include import decorator_include
from django.conf import settings
from django.urls import path

from utils.auth import support_authbearer_user

oauth2_endpoint_views = [*base_urlpatterns, *oidc_urlpatterns]
oauth2_endpoint_views += [
    path(
        "authorized_tokens/",
        decorator_include(
            support_authbearer_user,
            [
                path("", oauth2_views.AuthorizedTokensListView.as_view(), name="authorized-token-list"),
                path("<pk>/delete/", oauth2_views.AuthorizedTokenDeleteView.as_view(), name="authorized-token-delete"),
            ],
        ),
    ),
]

# only allow "manual" app management in debug mode
if settings.DEBUG:
    oauth2_endpoint_views += [
        path("applications/", oauth2_views.ApplicationList.as_view(), name="list"),
        path("applications/register/", oauth2_views.ApplicationRegistration.as_view(), name="register"),
        path("applications/<pk>/", oauth2_views.ApplicationDetail.as_view(), name="detail"),
        path("applications/<pk>/delete/", oauth2_views.ApplicationDelete.as_view(), name="delete"),
        path("applications/<pk>/update/", oauth2_views.ApplicationUpdate.as_view(), name="update"),
    ]
