"""Various utility template tags for the BMA project."""

from django import template
from django.conf import settings
from django.template.context import RequestContext
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def get_group_icons(
    context: RequestContext,
) -> str:
    """Return icons representing group memberships."""
    output = ""
    if settings.BMA_CREATOR_GROUP_NAME in context["request"].user.groups.values_list("name", flat=True):
        output += '<i class="fa-solid fa-user-ninja"></i> '
    if settings.BMA_MODERATOR_GROUP_NAME in context["request"].user.groups.values_list("name", flat=True):
        output += '<i class="fa-solid fa-user-shield"></i> '
    if settings.BMA_CURATOR_GROUP_NAME in context["request"].user.groups.values_list("name", flat=True):
        output += '<i class="fa-solid fa-user-astronaut"></i> '
    return mark_safe(output)  # noqa: S308
