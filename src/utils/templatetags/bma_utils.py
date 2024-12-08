"""Various utility template tags for the BMA project."""

from fractions import Fraction
from typing import TYPE_CHECKING

from django import template
from django.conf import settings
from django.template import loader
from django.template.context import RequestContext
from django.utils.safestring import mark_safe

from pictures.templatetags.pictures import picture
from pictures.utils import sizes

if TYPE_CHECKING:
    from django.db.models.fields.files import FieldFile

    from files.models import BaseFile
    from images.models import Image
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
def thumbnail(basefile: "BaseFile", width: int, ratio: str, mimetype: str = "image/webp") -> str:
    """BMA thumbnail tag. Depends on the hardcoded 50,100,150,200px (and 2x)."""
    from files.models import ThumbnailSource

    if width not in [50, 100, 150, 200]:
        return mark_safe(  # noqa: S308
            f"<!-- Error creating thumbnail markup, width {width} is not supported, "
            "only 50,100,150,200 is supported -->"
        )

    if ratio not in ThumbnailSource.source.field.aspect_ratios:  # type: ignore[attr-defined]
        return mark_safe(  # noqa: S308
            f"<!-- Error creating thumbnail markup, aspect ratio {ratio} is not supported, "
            f"only {ThumbnailSource.source.field.aspect_ratios} are supported -->"  # type: ignore[attr-defined]
        )
    t = None
    t2 = None
    for thumbnail in basefile.thumbnail_list:
        if thumbnail.mimetype != mimetype:
            continue
        if thumbnail.aspect_ratio != str(Fraction(ratio)):
            continue
        if thumbnail.width == width:
            t = thumbnail
            continue
        if thumbnail.width == width * 2:
            t2 = thumbnail
            continue

    if not t:
        # request size not available
        return mark_safe(  # noqa: S308
            '<img class="img-fluid img-thumbnail" '
            f'src="{settings.DEFAULT_THUMBNAIL_URLS[basefile.filetype]}" width="{width}">'
        )
    url = t.imagefile.url
    if t2:
        url2x = t2.imagefile.url
        url2x = f", {url2x} 2x"
    else:
        url2x = ""

    title = basefile.original_filename
    alt = basefile.description or basefile.original_filename
    return mark_safe(  # noqa: S308
        f'<img srcset="{url}{url2x}" src="{url}" '
        f'height="{t.height}" width="{width}" title="{title}" '
        f'alt="{alt}" class="img-fluid img-thumbnail">'
    )


@register.simple_tag()
def render_file(field_file: "PictureFieldFile | FieldFile", **kwargs: str) -> str:
    """Render a file."""
    if not hasattr(field_file.instance, "filetype"):
        output = "<!-- No filetype -->"
    elif field_file.instance.filetype == "image":
        output = picture(field_file=field_file, **kwargs)  # type: ignore[arg-type] # wtf?

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


@register.simple_tag()
def media_query(container_width: int | None = None, **kwargs: str) -> str:
    """Render a media query string based on the provided breakpoints and PICTURES breakpoints."""
    return str(sizes(container_width=container_width or settings.PICTURES["CONTAINER_WIDTH"], **kwargs))  # type: ignore[arg-type]


@register.simple_tag()
def render_source_set(*, image: "Image", mimetype: str, aspect_ratio: Fraction | None = None) -> str:
    """Return a source set for an image with all the versions of a given mimetype and AR."""
    output = ""
    # if aspect_ratio is None (no custom AR was requested): use the AR of the parent Image
    ratiokey = aspect_ratio or image.aspect_ratio
    versions = image.get_versions(mimetype=mimetype, aspect_ratio=aspect_ratio).get(ratiokey, {}).get(mimetype, {})
    for version in versions.values():
        output += f"{version.imagefile.url} {version.width}w, "
    # remove trailing ", "
    return output[:-2]
