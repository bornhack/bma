import requests
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.conf import settings

from .provider import CustomProvider


class CustomAdapter(OAuth2Adapter):
    provider_id = CustomProvider.id

    # Accessed by Django
    access_token_url = f"{settings.OAUTH_SERVER_BASEURL}/o/token/"
    profile_url = f"{settings.OAUTH_SERVER_BASEURL}/profile/api/"

    # Accessed by the user browser
    authorize_url = f"{settings.OAUTH_SERVER_BASEURL}/o/authorize/"

    def complete_login(self, request, app, token, **kwargs):
        headers = {"Authorization": "Bearer {0}".format(token.token)}
        resp = requests.get(self.profile_url, headers=headers)
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(CustomAdapter)
oauth2_callback = OAuth2CallbackView.adapter_view(CustomAdapter)
