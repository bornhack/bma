"""This module contains the BornHackViewAdapter class for the oauth2 login and callback views."""

from typing import Any

import requests
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.models import SocialToken
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView
from django.conf import settings
from django.http import HttpRequest

from .client import BornHackOAuth2Client


class BornHackViewAdapter(OAuth2Adapter):
    """View adapter class for the oauth2_login and oauth2_callback views."""

    provider_id = "bornhack"
    client_class = BornHackOAuth2Client

    # Accessed by Django
    access_token_url = f"{settings.OAUTH_SERVER_BASEURL}/o/token/"
    profile_url = f"{settings.OAUTH_SERVER_BASEURL}/profile/api/"

    # Accessed by the user browser
    authorize_url = f"{settings.OAUTH_SERVER_BASEURL}/o/authorize/"

    def complete_login(
        self, request: HttpRequest, app: SocialApp, token: SocialToken, **kwargs: dict[str, Any]
    ) -> SocialLogin:
        """Do an API call to get profile data before completing the login."""
        # add token to headers
        headers = {"Authorization": f"Bearer {token.token}"}
        # make HTTP request for the profile object
        resp = requests.get(self.profile_url, headers=headers, timeout=5)
        # parse json response
        extra_data = resp.json()
        # perfom social login
        return self.get_provider().sociallogin_from_response(request, extra_data)


# define the views using BornHackViewAdapter
oauth2_login = OAuth2LoginView.adapter_view(BornHackViewAdapter)
oauth2_callback = OAuth2CallbackView.adapter_view(BornHackViewAdapter)
