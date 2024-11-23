"""Widget related views."""

import uuid

from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from images.models import Image


def bma_widget_view(request: HttpRequest, style: str, count: int, uuid: str) -> HttpResponse:
    """Render a BMA widget rendered with the requested style, counter and UUID."""
    return render(
        request,
        f"{style}.js",
        context={"uuid": uuid, "count": count, "host": request.get_host()},
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
