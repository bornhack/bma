"""The BornHackSocialAccountAdapter takes care of populating fields in the BMA User model from the BornHack profile."""

from allauth.account.utils import user_field
from allauth.account.utils import user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.forms import Form
from django.http import HttpRequest
from django.urls import reverse
from django.utils.safestring import mark_safe

from users.models import User


class BornHackSocialAccountAdapter(DefaultSocialAccountAdapter):
    """The allauth SocialAccountAdapter for BornHack populates the BMA User with data from the BornHack profile."""

    provider_id = "bornhack"

    def is_open_for_signup(self, request: HttpRequest, sociallogin: SocialLogin) -> bool:
        """BMA is always open for social account signups."""
        return True

    def populate_user(self, request: HttpRequest, sociallogin: SocialLogin, data: dict[str, str]):  # type: ignore[no-untyped-def] # noqa: ANN201
        """Custom populate_user method to save extra fields from the BornHack profile.

        bornhack_allauth_provider.provider.BornHackProvider.extract_common_fields() is
        responsible for mapping the oidc claims to the data dict being used here.
        """
        # set username on the user object
        user_username(sociallogin.user, data.get("username"))

        # set initial handle on the user object to the bornhack username
        user_field(sociallogin.user, "handle", data["handle"])

        # set initial display_name on the user object to the bornhack profiles public_credit_name
        user_field(sociallogin.user, "display_name", data["public_credit_name"])

        # set description on the user object
        user_field(sociallogin.user, "description", data["description"])

        return sociallogin.user

    def save_user(self, request: HttpRequest, sociallogin: SocialLogin, form: Form | None = None) -> User:
        """Called on first login with a BornHack socialaccount."""
        user = super().save_user(request, sociallogin, form)
        # add to initial groups
        for group in settings.BMA_INITIAL_GROUPS:
            Group.objects.get(name=group).user_set.add(user)
        msg = (
            "This is your first login, welcome to BMA!<br><br>"
            "This page is your BMA settings page. Your profile below has been "
            "populated with some values taken from your BornHack account profile. "
            "You can change them below or come back to this page later."
        )
        if settings.BMA_INITIAL_GROUPS:
            msg += f"<br><br>Your user has been added to the following groups: {','.join(settings.BMA_INITIAL_GROUPS)}"
        messages.success(request, mark_safe(msg))  # noqa: S308
        return user  # type: ignore[no-any-return]

    def get_signup_redirect_url(self, request: HttpRequest) -> str:
        """Redirect to the profile after signup."""
        return reverse("users:user_profile", kwargs={"user_handle": request.user.handle})  # type: ignore[union-attr]
