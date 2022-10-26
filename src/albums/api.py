import logging
import operator
import uuid
from functools import reduce
from typing import List

from django.db.models import Q
from django.shortcuts import get_object_or_404
from guardian.shortcuts import assign_perm
from ninja import Query
from ninja import Router

from .models import Album
from .schema import AlbumFilters
from .schema import AlbumInSchema
from .schema import AlbumOutSchema
from utils.schema import MessageSchema

logger = logging.getLogger("bma")

# initialise API router
router = Router()

# https://django-ninja.rest-framework.com/guides/input/query-params/#using-schema
query = Query(...)


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

    # assign permissions
    assign_perm("change_album", request.user, album)
    assign_perm("delete_album", request.user, album)

    # return response
    return 201, album


@router.get(
    "/{album_uuid}/",
    response={200: AlbumOutSchema, 404: MessageSchema},
    summary="Return an album.",
    auth=None,
)
def album_get(request, album_uuid: uuid.UUID):
    """Return an album."""
    return get_object_or_404(Album, uuid=album_uuid)


@router.get(
    "/",
    response={200: List[AlbumOutSchema]},
    summary="Return a list of albums.",
    auth=None,
)
def album_list(request, filters: AlbumFilters = query):
    """Return a list of albums."""
    albums = Album.objects.all()

    if filters.files:
        # __in is OR and we want AND, build a query for .exclude() with all file UUIDs
        query = reduce(operator.and_, (Q(files__uuid=uuid) for uuid in filters.files))
        albums = albums.exclude(~query)

    if filters.search:
        albums = albums.filter(title__icontains=filters.search) | albums.filter(
            description__icontains=filters.search,
        )

    if filters.sorting:
        if filters.sorting.endswith("_asc"):
            # remove _asc and add +
            albums = albums.order_by(f"{filters.sorting[:-4]}")
        else:
            # remove _desc and add -
            albums = albums.order_by(f"-{filters.sorting[:-5]}")

    if filters.offset:
        albums = albums[filters.offset :]

    if filters.limit:
        albums = albums[: filters.limit]

    return albums


@router.put(
    "/{album_uuid}/",
    response={
        200: AlbumOutSchema,
        202: MessageSchema,
        403: MessageSchema,
        404: MessageSchema,
    },
    operation_id="albums_api_album_update_put",
    summary="Replace an album.",
)
@router.patch(
    "/{album_uuid}/",
    response={
        200: AlbumOutSchema,
        202: MessageSchema,
        403: MessageSchema,
        404: MessageSchema,
    },
    operation_id="albums_api_album_update_patch",
    summary="Update an album.",
)
def album_update(
    request,
    album_uuid: uuid.UUID,
    payload: AlbumInSchema,
    check: bool = None,
):
    """Update (PATCH) or replace (PUT) an Album."""
    album = get_object_or_404(Album, uuid=album_uuid)
    if not request.user.has_perm("change_album", album):
        # no permission
        return 403, {"message": "Permission denied."}
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    if request.method == "PATCH":
        # we are updating the object, we do not want defaults for absent fields
        data = payload.dict(exclude_unset=True)
        # handle the m2m seperate
        del data["files"]
        Album.objects.filter(uuid=album.uuid).update(**data)
        album.refresh_from_db()
    else:
        # we are replacing the object, we do want defaults for absent fields
        for attr, value in payload.dict(exclude_unset=False).items():
            if attr == "files":
                # handle the m2m seperate
                continue
            else:
                setattr(album, attr, value)
        album.save()
    if "files" in payload.dict():
        album.files.set(payload.dict()["files"])
    return album


@router.delete(
    "/{album_uuid}/",
    response={202: MessageSchema, 204: None, 403: MessageSchema, 404: MessageSchema},
    summary="Delete an album.",
)
def album_delete(request, album_uuid: uuid.UUID, check: bool = None):
    album = get_object_or_404(Album, uuid=album_uuid)
    if not request.user.has_perm("delete_album", album):
        # no permission
        return 403, {"message": "Permission denied."}
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    album.delete()
    return 204, None
