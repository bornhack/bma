"""This module contains the BornHackProvider class and BornHackAccount classes."""

from allauth.socialaccount.providers.openid_connect.provider import OpenIDConnectProvider


class BornHackProvider(OpenIDConnectProvider):
    """The BornHackProvider for using bornhack.dk oidc.

    This class defines overrides for OpenIDConnectProvider to make everything work:
      - Extract user id
      - Extract data from userinfo claims
      - Set default scopes
    """

    id = "bornhack"
    name = "BornHack"

    def extract_uid(self, data: dict[str, str]) -> str:
        """Get BornHack username from the OIDC standard claim 'sub'."""
        return str(data["userinfo"]["sub"])

    def extract_common_fields(self, data: dict[str, str]) -> dict[str, str]:
        """Map OIDC user claims to the data dict used in BornHackSocialAccountAdapter.populate_user()."""
        return {
            # standard OIDC user claims
            "username": str(data["userinfo"]["sub"]),
            "handle": str(data["userinfo"].get("preferred_username", "")),
            # custom BornHack user claims
            "description": str(data["userinfo"].get("bornhack:v2:description", "")),
            "public_credit_name": str(data["userinfo"].get("bornhack:v2:public_credit_name", "BMA user")),
        }


provider_classes = [BornHackProvider]
