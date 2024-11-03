"""AllAuth DefaultAccountAdapter subclass used to deny local BMA account creation. Only social accounts are allowed."""

from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpRequest


class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    """Adapter to deny new local signups."""

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """Deny local signups."""
        return False
