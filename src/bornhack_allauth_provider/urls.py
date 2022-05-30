from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import BornHackProvider

urlpatterns = default_urlpatterns(BornHackProvider)
