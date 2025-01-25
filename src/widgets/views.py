"""Widget related views."""

import json
import uuid

from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from albums.models import Album
from files.models import BaseFile
from images.models import Image


def serialise_basefile(file: BaseFile) -> dict[str, int | str | dict[str, str | dict[str, str]]]:
    """Serialise a BaseFile object into a JSON-serialisable dictionary."""
    json_data = {
        "uuid": str(file.uuid),
        "title": file.title,
        "description": file.description,
        "links": file.resolve_links(),
        "filename": file.filename,
        "filetype": file.filetype,
        "filetype_icon": file.filetype_icon,
        "license": file.license,
        "license_name": file.license_name,
        "license_url": file.license_url,
        "attribution": file.attribution,
    }
    if file.filetype == "image":
        json_data.update(
            {
                "aspect_ratio": file.aspect_ratio,
                "exif": file.exif,
                "width": file.width,
                "height": file.height,
            }
        )
    return json_data


def bma_widget_view(request: HttpRequest, style: str, count: int, uuid: str) -> HttpResponse:
    """Render a BMA widget rendered with the requested style, counter and UUID."""
    js_files = []
    try:
        album = Album.bmanager.get(pk=uuid)
        js_files = [serialise_basefile(file) for file in album.active_files_list if file.permitted(user=request.user)]
    except Album.DoesNotExist:
        try:
            file = BaseFile.bmanager.get(uuid=uuid)
            if file.permitted(user=request.user):
                js_files.append(serialise_basefile(file))
        except BaseFile.DoesNotExist:
            pass

    return render(
        request,
        f"{style}.js",
        context={"uuid": uuid, "files": json.dumps(js_files), "count": count, "host": request.get_host()},
        content_type="text/javascript",
    )


def bma_widget_iframe_view(request: HttpRequest, style: str, option: int, uuid: str) -> HttpResponse:
    """Render a BMA iframe widget rendered with the requested style, counter and UUID."""
    js_files = []
    try:
        album = Album.bmanager.get(pk=uuid)
        js_files = BaseFile.bmanager.filter(
            uuid__in=[f.uuid for f in album.active_files_list if f.permitted(user=request.user)]
        )
    except Album.DoesNotExist:
        try:
            file = BaseFile.bmanager.get(uuid=uuid)
            if file.permitted(user=request.user):
                js_files.append(serialise_basefile(file))
        except BaseFile.DoesNotExist:
            pass

    return render(
        request,
        f"{style}.html",
        context={"uuid": uuid, "files": js_files, "option": option, "host": request.get_host()},
    )


def picture_embed_view(request: HttpRequest, image_uuid: uuid.UUID) -> HttpResponse:
    """Return a <picture> tag in an empty HTML body suitable for iframe use."""
    image = get_object_or_404(Image, uuid=image_uuid)
    return render(
        request,
        "picture.html",
        context={"image": image},
    )
