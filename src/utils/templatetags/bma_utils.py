"""Various utility template tags for the BMA project."""

from fractions import Fraction
from typing import TYPE_CHECKING

from django import template
from django.conf import settings
from django.template import loader
from django.utils.safestring import mark_safe

from pictures.templatetags.pictures import picture
from pictures.utils import sizes

if TYPE_CHECKING:
    from django.db.models.fields.files import FieldFile

    from files.models import BaseFile
    from images.models import Image
    from pictures.models import PictureFieldFile
    from users.models import User

register = template.Library()


@register.simple_tag()
def get_group_icons(user: "User") -> str:
    """Return icons representing group memberships."""
    output = ""
    if settings.BMA_CREATOR_GROUP_NAME in user.cached_groups:
        output += '<i title="Creator" class="fa-solid fa-user-ninja"></i> '
    if settings.BMA_MODERATOR_GROUP_NAME in user.cached_groups:
        output += '<i title="Moderator" class="fa-solid fa-user-shield"></i> '
    if settings.BMA_CURATOR_GROUP_NAME in user.cached_groups:
        output += '<i title="Curator" class="fa-solid fa-user-astronaut"></i> '
    if settings.BMA_WORKER_GROUP_NAME in user.cached_groups:
        output += '<i title="Worker" class="fa-solid fa-user-gear"></i> '
    return mark_safe(output)  # noqa: S308


@register.simple_tag()
def thumbnail(  # noqa: PLR0913
    basefile: "BaseFile",
    width: int,
    ratio: str,
    mimetype: str = "image/webp",
    *,
    noscript: bool = False,
    prefix: str = "",
) -> str:
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
    url2x = ""
    for thumbnail in basefile.thumbnail_list:
        if thumbnail.mimetype != mimetype:
            continue
        if thumbnail.aspect_ratio != str(Fraction(ratio)):
            continue
        if thumbnail.width == width:
            t = thumbnail
            continue
        if thumbnail.width == width * 2:
            url2x = f", {prefix}{thumbnail.imagefile.url} 2x"
            continue

    if not t:
        # request size not available
        return mark_safe(  # noqa: S308
            '<img class="img-fluid img-thumbnail" '
            f'src="{prefix}{settings.DEFAULT_THUMBNAIL_URLS[basefile.filetype]}" width="{width}">'
        )

    title = f"""{basefile.title}
{basefile.attribution}
{basefile.license}"""
    hoverclass = "zoom" if basefile.filetype in ["image", "document"] else "play"
    tmpl = loader.get_template("thumbnail.html" if not noscript else "thumbnail_noscript.html")
    output = tmpl.render(
        {
            "url": f"{prefix}{t.imagefile.url}",
            "url2x": url2x,
            "hoverclass": hoverclass,
            "width": width,
            "height": t.height,
            "title": title,
            "file": basefile,
            "alt": title,
        }
    )
    return mark_safe(output)  # noqa: S308


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
