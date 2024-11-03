"""Auth classes for BMA."""

from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import TypeVar

from django.contrib.auth.models import AnonymousUser
from ninja.security import HttpBearer
from oauth2_provider.oauth2_backends import get_oauthlib_core

if TYPE_CHECKING:
    from django.http import HttpRequest
from mypy_extensions import NamedArg

T = TypeVar("T")


class BMAuthBearer(HttpBearer):
    """Bearer auth for django-ninja. Check token and set request.user.

    The HttpBearer base class makes sure this code is only called when there is
    an "Authorization: Bearer ...." header in the request.

    - If the token is valid request.user is set to the user owning the token.
    - If the token is invalid return None triggering a 401 response from ninja
    or passing to the next auth module.

    Used as auth on all django-ninja endpoints (set on the router).
    """

    def authenticate(self, request: "HttpRequest", token: str) -> bool:
        """Authenticate the request, set request.user, return bool."""
        oauthlib_core = get_oauthlib_core()
        valid, oauth = oauthlib_core.verify_request(request, scopes=[])
        if not valid:
            return False
        request.user = oauth.user
        return True


# https://docs.python.org/3/library/typing.html#annotating-callable-objects
def support_authbearer_user(
    view_func: Callable[[NamedArg("HttpRequest", "request"), NamedArg(str, "path"), NamedArg(bool, "accel")], T],
) -> Callable[["HttpRequest", str, bool], T]:
    """View decorator to set request.user if there is a valid auth Bearer token.

    Use this decorator on plain/non-ninja views where functional bearer token auth
    is desired.

    This decorator does nothing in case of invalid or missing auth tokens. Django
    will set request.user to session user for sessioncookie authenticated requests,
    and to AnonymousUser for unauthenticated requests.

    This decorator can be used together with login_required and other decorators.
    """

    def wrapper(request: "HttpRequest", *args, **kwargs) -> T:  # type: ignore[no-untyped-def] # noqa: ANN002,ANN003
        """Get oauthlib core, validate request, set request.user if token is good."""
        oauthlib_core = get_oauthlib_core()
        valid, oauth_response = oauthlib_core.verify_request(request, scopes=[])
        if valid:
            # token is valid, set request.user
            request.user = oauth_response.user
        # call the decorated view and return the response
        return view_func(request=request, *args, **kwargs)  # noqa: B026

    return wrapper


def permit_anonymous_api_use(request: "HttpRequest") -> AnonymousUser:
    """Allow unauthenticated access to django-ninja API endpoints.

    Can be used alone for endpoints where auth is irrelevant, or with BMAuthBearer when
    an endpoint should be accessible for both authenticated and unauthenticated users.
    """
    user = AnonymousUser()
    request.user = user
    return user
