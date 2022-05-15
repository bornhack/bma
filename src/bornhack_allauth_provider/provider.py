from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class CustomAccount(ProviderAccount):
    """No changes yet."""


class CustomProvider(OAuth2Provider):

    id = "bornhackprovider"
    name = "BornHack"
    account_class = CustomAccount

    def extract_uid(self, data):
        return str(data["user"]["user_id"])

    def extract_common_fields(self, data):
        return {
            "username": data["user"]["username"],
            "email": data["user"]["username"],
            "public_credit_name": data["profile"]["public_credit_name"],
            "description": data["profile"]["description"],
        }

    def get_default_scope(self):
        scope = ["profile:read"]
        return scope


providers.registry.register(CustomProvider)
