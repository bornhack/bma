"""Various utility template tags for the BMA project."""

from typing import TYPE_CHECKING

from django import template
from django.conf import settings
from django.template.context import RequestContext
from django.utils.safestring import mark_safe

if TYPE_CHECKING:
    from pictures.models import PictureFieldFile

register = template.Library()


@register.simple_tag(takes_context=True)
def get_group_icons(
    context: RequestContext,
) -> str:
    """Return icons representing group memberships."""
    output = ""
    if settings.BMA_CREATOR_GROUP_NAME in context["request"].user.cached_groups:
        output += '<i class="fa-solid fa-user-ninja"></i> '
    if settings.BMA_MODERATOR_GROUP_NAME in context["request"].user.cached_groups:
        output += '<i class="fa-solid fa-user-shield"></i> '
    if settings.BMA_CURATOR_GROUP_NAME in context["request"].user.cached_groups:
        output += '<i class="fa-solid fa-user-astronaut"></i> '
    return mark_safe(output)  # noqa: S308


@register.simple_tag()
def thumbnail(field_file: "PictureFieldFile", width: int, ratio: str | None = None) -> str:
    """BMA thumbnail tag. Depends on the hardcoded 50,100,150,200px (and 2x)."""
    if width not in [50, 100, 150, 200]:
        raise ValueError(width)
    if ratio not in field_file.field.aspect_ratios:
        raise ValueError(ratio)
    url = field_file.aspect_ratios[ratio]["WEBP"][width].url
    url2x = field_file.aspect_ratios[ratio]["WEBP"][width * 2].url
    height = field_file.aspect_ratios[ratio]["WEBP"][width].height
    title = field_file.instance.basefile.original_filename
    alt = field_file.instance.basefile.description or field_file.instance.basefile.original_filename
    return mark_safe(  # noqa: S308
        f'<img srcset="{url}, {url2x} 2x" src="{url}" height="{height}" width="{width}" title="{title}" alt="{alt}">'
    )
