from allauth.account.utils import user_field
from allauth.account.utils import user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class BornHackSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, socialaccount):
        return True

    def populate_user(self, request, sociallogin, data):
        """Custom populate_user() method to save our extra fields."""
        user = sociallogin.user

        # get username
        username = data.get("username")
        user_username(user, username or "")

        # get public_credit_name
        public_credit_name = data.get("public_credit_name")
        user_field(user, "public_credit_name", public_credit_name)

        # get description
        description = data.get("description")
        user_field(user, "description", description)
        return user
