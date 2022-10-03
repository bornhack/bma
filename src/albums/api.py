import logging
import uuid
from typing import List

from django.shortcuts import get_object_or_404
from ninja import Router

from .models import Album
from .schema import AlbumInSchema
from .schema import AlbumOutSchema
from utils.schema import MessageSchema

logger = logging.getLogger("bma")

# initialise API router
router = Router()


@router.post(
    "/albums/",
    response={201: AlbumOutSchema},
    summary="Create a new album",
)
def album_create(request, payload: AlbumInSchema):
    """Use this endpoint to create a new album, with or without files."""
    album = Album()
    for k, v in payload.dict().items():
        if k == "files":
            album.files.set(v)
        else:
            setattr(album, k, v)
    album.owner = request.user
    album.save()
    return 201, album


@router.get(
    "/{album_uuid}/",
    response={200: AlbumOutSchema, 404: MessageSchema},
    summary="Return an album.",
)
def album_get(request, album_uuid: uuid.UUID):
    """Return an album."""
    return get_object_or_404(Album, uuid=album_uuid)


@router.get(
    "/",
    response={200: List[AlbumOutSchema]},
    summary="Return a list of albums.",
)
def album_list(request):
    """Return a list of albums."""
    return Album.objects.all()


@router.put(
    "/{album_uuid}/",
    response={200: AlbumOutSchema, 403: MessageSchema, 404: MessageSchema},
    operation_id="albums_api_album_update_put",
    summary="Replace an album.",
)
@router.patch(
    "/{album_uuid}/",
    response={200: AlbumOutSchema, 403: MessageSchema, 404: MessageSchema},
    operation_id="albums_api_album_update_patch",
    summary="Update an album.",
)
def album_update(request, album_uuid: uuid.UUID, payload: AlbumInSchema):
    """Update (PATCH) or replace (PUT) an Album."""
    album = get_object_or_404(Album, uuid=album_uuid)
    if album.owner != request.user:
        return 403, {"message": f"No permission to update album {album_uuid}"}
    # include defaults for optional fields absent in api call?
    if request.method == "PATCH":
        # we do not want defaults for absent fields
        exclude_unset = True
    else:
        # we want defaults for absent fields
        exclude_unset = False
    # loop over and set values, treat m2m special
    for attr, value in payload.dict(exclude_unset=exclude_unset).items():
        if attr == "files":
            # use .set() to save the m2m
            album.files.set(value)
        else:
            setattr(album, attr, value)
    album.save()
    return album


@router.delete(
    "/{album_uuid}/",
    response={204: None, 403: MessageSchema, 404: MessageSchema},
    summary="Delete an album.",
)
def album_delete(request, album_uuid: uuid.UUID):
    album = get_object_or_404(Album, uuid=album_uuid)
    if album.owner != request.user:
        return 403, {"message": f"No permission to delete album {album_uuid}"}
    album.delete()
    return 204, None
