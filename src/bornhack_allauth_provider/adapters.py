"""The BornHackSocialAccountAdapter takes care of populating fields in the BMA User model from the BornHack profile."""
from allauth.account.utils import user_field
from allauth.account.utils import user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.utils import build_absolute_uri
from django.conf import settings
from django.contrib.auth.models import Group
from django.forms import Form
from django.http import HttpRequest
from django.urls import reverse
from users.models import User

from .client import BornHackOAuth2Client


class BornHackSocialAccountAdapter(DefaultSocialAccountAdapter):
    """The allauth SocialAccountAdapter for BornHack populates the BMA User with data from the BornHack profile."""

    provider_id = "bornhack"
    client_class = BornHackOAuth2Client
    access_token_method = "POST"  # noqa: S105
    access_token_url = f"{settings.OAUTH_SERVER_BASEURL}/o/token/"
    authorize_url = f"{settings.OAUTH_SERVER_BASEURL}/o/authorize/"
    scope_delimiter = ","
    basic_auth = False
    headers: dict[str, str] | None = None

    def is_open_for_signup(self, request: HttpRequest, sociallogin: SocialLogin) -> bool:
        """Always open for business."""
        return True

    def populate_user(self, request: HttpRequest, sociallogin: SocialLogin, data: dict[str, str]):  # type: ignore[no-untyped-def] # noqa: ANN201
        """Custom populate_user method to save our extra fields from the BornHack profile."""
        # set username on the user object
        user_username(sociallogin.user, data.get("username"))

        # set public_credit_name on the user object
        user_field(sociallogin.user, "public_credit_name", data.get("public_credit_name"))

        # set description on the user object
        user_field(sociallogin.user, "description", data.get("description"))

        return sociallogin.user

    def save_user(self, request: HttpRequest, sociallogin: SocialLogin, form: Form | None = None) -> User:
        """Called on first login with a BornHack socialaccount."""
        user = super().save_user(request, sociallogin, form)
        # add to curators group
        curators, created = Group.objects.get_or_create(name=settings.BMA_CURATOR_GROUP_NAME)
        curators.user_set.add(user)
        return user  # type: ignore[no-any-return]

    def get_client(self, request: HttpRequest, app: SocialApp) -> OAuth2Client:
        """Generate callback url, initialise and return client."""
        callback_url = self.get_callback_url(request, app)
        return self.client_class(
            self.request,
            app.client_id,
            app.secret,
            self.access_token_method,
            self.access_token_url,
            callback_url,
            scope_delimiter=self.scope_delimiter,
            headers=self.headers,
            basic_auth=self.basic_auth,
        )

    def get_callback_url(self, request: HttpRequest, app: SocialApp) -> str:
        """Callback url."""
        callback_url = reverse(self.provider_id + "_callback")
        return build_absolute_uri(request, callback_url, "https" if request.is_secure() else "http")  # type: ignore[no-any-return]
