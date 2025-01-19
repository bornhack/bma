"""Widget related views."""

import json
import uuid

from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from albums.models import Album
from images.models import Image


def bma_widget_view(request: HttpRequest, style: str, count: int, uuid: str) -> HttpResponse:
    """Render a BMA widget rendered with the requested style, counter and UUID."""
    js_files = []
    try:
        album = Album.bmanager.get(pk=uuid)
        js_files = [
            {
                "uuid": str(item.uuid),
                "title": item.title,
                "description": item.description,
                "filename": item.filename,
                "filetype": item.filetype,
                "filetype_icon": item.filetype_icon,
                "aspect_ratio": item.aspect_ratio,
                "license": item.license,
                "license_name": item.license_name,
                "license_url": item.license_url,
                "attribution": item.attribution,
                "exif": item.exif,
                "links": item.resolve_links(),
                "width": item.width,
                "height": item.height,
            }
            for item in album.active_files_list
        ]
    except Album.DoesNotExist:
        item = get_object_or_404(Image, uuid=uuid)
        js_files.append(
            {
                "uuid": str(item.uuid),
                "title": item.title,
                "description": item.description,
                "filename": item.filename,
                "filetype": item.filetype,
                "filetype_icon": item.filetype_icon,
                "aspect_ratio": item.aspect_ratio,
                "license": item.license,
                "license_name": item.license_name,
                "license_url": item.license_url,
                "attribution": item.attribution,
                "exif": item.exif,
                "links": item.resolve_links(),
                "width": item.width,
                "height": item.height,
            }
        )

    return render(
        request,
        f"{style}.js",
        context={"uuid": uuid, "files": json.dumps(js_files), "count": count, "host": request.get_host()},
        content_type="text/javascript",
    )


def picture_embed_view(request: HttpRequest, image_uuid: uuid.UUID) -> HttpResponse:
    """Return a <picture> tag in an empty HTML body suitable for iframe use."""
    image = get_object_or_404(Image, uuid=image_uuid)
    return render(
        request,
        "picture.html",
        context={"image": image},
    )
