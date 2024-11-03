"""This module contains the BornHackProvider class and BornHackAccount classes."""

from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

from .adapters import BornHackSocialAccountAdapter


class BornHackAccount(ProviderAccount):
    """The BornHackAccount class only defines the to_str() method to find the username."""

    def to_str(self) -> str:
        """Get the username from extra_data."""
        return str(self.account.extra_data["user"]["username"])


class BornHackProvider(OAuth2Provider):
    """The BornHackProvider."""

    id = "bornhack"
    name = "BornHack"
    account_class = BornHackAccount
    oauth2_adapter_class = BornHackSocialAccountAdapter

    def extract_uid(self, data: dict[str, dict[str, str]]) -> str:
        """Get user_id from the user object."""
        return str(data["user"]["user_id"])

    def extract_common_fields(self, data: dict[str, dict[str, str]]) -> dict[str, str]:
        """Override extract_common_fields to get the data to be used by populate_user()."""
        return {
            "username": data["user"]["username"],
            "public_credit_name": data["profile"]["public_credit_name"],
            "description": data["profile"]["description"],
        }

    def get_default_scope(self) -> list[str]:
        """The only scope we need is profile:read."""
        return ["profile:read"]


provider_classes = [BornHackProvider]
