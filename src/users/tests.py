"""Tests for the users app."""

from django.conf import settings
from oauth2_provider.models import get_application_model

from utils.tests import BmaTestBase

Application = get_application_model()


class TestUserOauthApplication(BmaTestBase):
    """Tests for oauth stuff."""

    def test_user_oauth_app_for_webapp(self) -> None:
        """Make sure the webapp oauth app has been created correctly for all users."""
        redirect_uris = [f"https://{hostname}/api/csrf/" for hostname in settings.ALLOWED_HOSTS]
        for user in self.users:
            app = Application.objects.get(name="autocreated-bma-webapp-client", user=user)
            assert app.redirect_uris == " ".join(redirect_uris)
            assert app.client_type == "public"
            assert app.authorization_grant_type == "authorization-code"
            assert app.skip_authorization
            assert hasattr(self.user0, "webapp_oauth_client_id")
