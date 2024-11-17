"""Convenience function to use the querystring templatetag from python."""

from typing import TYPE_CHECKING

from django.template import RequestContext
from django.template.defaulttags import querystring  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from django.http import HttpRequest


def querystring_from_request(request: "HttpRequest", **kwargs: str) -> str:
    """Convenience function to use the querystring templatetag from python."""
    context = RequestContext(request)
    return str(querystring(context, **kwargs))
