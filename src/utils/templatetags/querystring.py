"""Templatetag for working with querystrings in templates.

Taken from https://github.com/django/django/commit/e67d3580edbee1a4b58d40875293714ac3fc6937
Remove when django 5.1 is out
"""


from collections.abc import Iterable
from typing import Any

from django import template
from django.http import QueryDict
from django.template.context import RequestContext

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(
    context: RequestContext,
    query_dict: QueryDict | None = None,
    **kwargs: dict[str, str | None | Iterable[Any] | bytes],
) -> str:
    """Add, remove, and change parameters of a ``QueryDict``.

    Return the result as a query string. If the ``query_dict`` argument
    is not provided, default to ``request.GET``.

    For example::
        {% query_string foo=3 %}
    To remove a key::
        {% query_string foo=None %}
    To use with pagination::
        {% query_string page=page_obj.next_page_number %}
    A custom ``QueryDict`` can also be used::
        {% query_string my_query_dict foo=3 %}
    """
    if query_dict is None:
        query_dict = context.request.GET
    query_dict = query_dict.copy()
    for key, value in kwargs.items():
        if value is None:
            if key in query_dict:
                del query_dict[key]
        elif isinstance(value, Iterable) and not isinstance(value, str):
            query_dict.setlist(key, value)
        else:
            query_dict[key] = value
    if not query_dict:
        return ""
    query_string = query_dict.urlencode()
    return f"?{query_string}"
