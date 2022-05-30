from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class BornHackAccount(ProviderAccount):
    def to_str(self):
        return self.account.extra_data["user"]["username"]


class BornHackProvider(OAuth2Provider):

    id = "bornhack"
    name = "BornHack"
    account_class = BornHackAccount

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


providers.registry.register(BornHackProvider)
