"""Various utility template tags for the BMA project."""

from typing import TYPE_CHECKING

from django import template
from django.conf import settings
from django.template import loader
from django.template.context import RequestContext
from django.utils.safestring import mark_safe
from pictures.templatetags.pictures import picture

if TYPE_CHECKING:
    from django.db.models.fields.files import FieldFile
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
def thumbnail(field_file: "PictureFieldFile", filetype: str, width: int, ratio: str | None = None) -> str:
    """BMA thumbnail tag. Depends on the hardcoded 50,100,150,200px (and 2x)."""
    if isinstance(field_file, str):
        return mark_safe(  # noqa: S308
            f'<img class="img-fluid img-thumbnail" src="{settings.DEFAULT_THUMBNAIL_URLS[filetype]}" width="{width}">'
        )

    if width not in [50, 100, 150, 200]:
        return mark_safe(  # noqa: S308
            f"<!-- Error creating thumbnail markup, width {width} is not supported, "
            "only 50,100,150,200 is supported -->"
        )

    if ratio not in field_file.field.aspect_ratios:
        return mark_safe(  # noqa: S308
            f"<!-- Error creating thumbnail markup, aspect ratio {ratio} is not supported, "
            f"only {field_file.field.aspect_ratios} are supported -->"
        )

    url = field_file.aspect_ratios[ratio]["WEBP"][width].url
    url2x = field_file.aspect_ratios[ratio]["WEBP"][width * 2].url
    height = field_file.aspect_ratios[ratio]["WEBP"][width].height
    title = field_file.instance.basefile.original_filename
    alt = field_file.instance.basefile.description or field_file.instance.basefile.original_filename
    return mark_safe(  # noqa: S308
        f'<img srcset="{url}, {url2x} 2x" src="{url}" '
        f'height="{height}" width="{width}" title="{title}" '
        f'alt="{alt}" class="img-fluid img-thumbnail">'
    )


@register.simple_tag()
def render_file(field_file: "PictureFieldFile | FieldFile", **kwargs: str) -> str:
    """Render a file."""
    if not hasattr(field_file.instance, "filetype"):
        output = "<!-- No filetype -->"
    elif field_file.instance.filetype == "image":
        output = picture(field_file=field_file, **kwargs)

    elif field_file.instance.filetype == "audio":
        tmpl = loader.get_template("includes/render_audio.html")
        output = tmpl.render(
            {
                "url": field_file.url,
            }
        )
    elif field_file.instance.filetype == "video":
        tmpl = loader.get_template("includes/render_video.html")
        output = tmpl.render(
            {
                "url": field_file.url,
            }
        )
    elif field_file.instance.filetype == "document":
        tmpl = loader.get_template("includes/render_document.html")
        output = tmpl.render(
            {
                "url": field_file.url,
                **kwargs,
            }
        )
    else:
        output = "<!-- Unknown filetype -->"
    return mark_safe(output)  # noqa: S308
