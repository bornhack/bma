import requests
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView
from django.conf import settings

from .provider import BornHackProvider


class BornHackAdapter(OAuth2Adapter):
    provider_id = BornHackProvider.id

    # Accessed by Django
    access_token_url = f"{settings.OAUTH_SERVER_BASEURL}/o/token/"
    profile_url = f"{settings.OAUTH_SERVER_BASEURL}/profile/api/"

    # Accessed by the user browser
    authorize_url = f"{settings.OAUTH_SERVER_BASEURL}/o/authorize/"

    # def is_open_for_signup(self, request, socialaccount):
    #    return True

    def complete_login(self, request, app, token, **kwargs):
        headers = {"Authorization": f"Bearer {token.token}"}
        resp = requests.get(self.profile_url, headers=headers)
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(BornHackAdapter)
oauth2_callback = OAuth2CallbackView.adapter_view(BornHackAdapter)
