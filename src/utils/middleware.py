from ninja.operation import PathView


class ExemptOauthFromCSRFMiddleware:
    """This middleware disables CSRF auth for non-session authed requests for Ninja views.
    We only want (need) CSRF enabled if the request session-cookie authed.
    This is needed because django-ninja does not support enabling/disabling CSRF based on auth type.
    https://github.com/vitalik/django-ninja/issues/283
    """

    def __init__(self, get_response):
        """Boilerplate."""
        self.get_response = get_response

    def __call__(self, request):
        """Boilerplate."""
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Disable CSRF auth for non-cookie authenticated requests to Ninja."""
        # skip if user is session authenticated,
        # meaning any cookie auth requests will require csrf
        if request.user.is_authenticated:
            return

        # we now know this request is not session authenticated,
        # so we can safely disable CSRF checks. Do so if this is
        # a ninja view.

        # first get the view class
        klass = getattr(view_func, "__self__", None)
        if not klass:
            return

        # make sure view class is Ninjas PathView
        if isinstance(klass, PathView):
            # disable CSRF check for this request
            request._dont_enforce_csrf_checks = True
