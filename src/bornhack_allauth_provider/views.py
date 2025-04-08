"""This module hooks up the default allauth views."""

from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView

oauth2_login = OAuth2LoginView.as_view()
oauth2_callback = OAuth2CallbackView
