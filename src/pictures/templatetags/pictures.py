"""The picture templatetag."""

from typing import TYPE_CHECKING

from django import template
from django.template import loader

from pictures import utils

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from images.models import ImageVersion
    from pictures.models import PictureFieldFile

register = template.Library()


@register.simple_tag()
def picture(
    field_file: "PictureFieldFile",
    img_alt: str = "",
    ratio: str = "",
    container: int | None = None,
    **kwargs: dict[str, str],
) -> str:
    """Render a <picture> tag for the given Image."""
    container = container or field_file.field.container_width  # type: ignore[assignment]
    tmpl = loader.get_template("pictures/picture.html")
    breakpoints = {}
    picture_attrs = {}
    img_attrs = {
        "src": field_file.url,
        "alt": img_alt,
        "width": field_file.width,
        "height": field_file.height,
    }
    # use AR of the original image if no custom AR was requested
    if not ratio:
        ratio = field_file.instance.aspect_ratio  # type: ignore[attr-defined]

    # loop over kwargs (breakpoints, picture_ attrs, or img_ attrs)
    for key, value in kwargs.items():
        if key in field_file.field.breakpoints:  # type: ignore[operator]
            breakpoints[key] = value
        elif key.startswith("picture_"):
            picture_attrs[key[8:]] = value
        elif key.startswith("img_"):
            img_attrs[key[4:]] = value
        else:
            raise ValueError(key)

    sources: dict[str, QuerySet[ImageVersion]] = {}
    for mimetype in field_file.instance.image_versions.values_list("mimetype", flat=True):  # type: ignore[attr-defined]
        sources[mimetype] = field_file.instance.image_versions.filter(mimetype=mimetype, aspect_ratio=ratio)  # type: ignore[attr-defined]

    return tmpl.render(
        {
            "field_file": field_file,
            "alt": img_alt,
            "sources": sources,
            "media": utils.sizes(
                columns=field_file.field.grid_columns,  # type: ignore[arg-type]
                container_width=container,
                settings=field_file.field.breakpoints,  # type: ignore[arg-type]
                **breakpoints,  # type: ignore[arg-type]
            ),
            "picture_attrs": picture_attrs,
            "img_attrs": img_attrs,
        }
    )
