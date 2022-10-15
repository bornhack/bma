import logging
import uuid
from typing import List
from typing import Union

import magic
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from guardian.shortcuts import assign_perm
from guardian.shortcuts import get_objects_for_user
from ninja import Query
from ninja import Router
from ninja.files import UploadedFile

from .models import BaseFile
from .schema import FileFilters
from .schema import FileOutSchema
from .schema import FileTypeChoices
from .schema import FileUpdateSchema
from .schema import UploadMetadata
from audios.models import Audio
from audios.schema import AudioOutSchema
from documents.models import Document
from documents.schema import DocumentOutSchema
from pictures.models import Picture
from pictures.schema import PictureOutSchema
from utils.schema import MessageSchema
from videos.models import Video
from videos.schema import VideoOutSchema


logger = logging.getLogger("bma")

# initialise API router
router = Router()

# https://django-ninja.rest-framework.com/guides/input/query-params/#using-schema
query = Query(...)


@router.post(
    "/upload/",
    response={
        201: Union[PictureOutSchema, VideoOutSchema, AudioOutSchema, DocumentOutSchema],
        403: MessageSchema,
        422: MessageSchema,
    },
    summary="Upload a new file",
)
def upload(request, f: UploadedFile, metadata: UploadMetadata):
    """API endpoint for file uploads."""
    # find the filetype using libmagic by reading the first bit of the file
    mime = magic.from_buffer(f.read(512), mime=True)

    if mime in settings.ALLOWED_PICTURE_TYPES:
        from pictures.models import Picture as Model
    elif mime in settings.ALLOWED_VIDEO_TYPES:
        from videos.models import Video as Model
    elif mime in settings.ALLOWED_AUDIO_TYPES:
        from audios.models import Audio as Model
    elif mime in settings.ALLOWED_DOCUMENT_TYPES:
        from documents.models import Document as Model
    else:
        # file type not supported, return error
        return 422, {"message": "File type not supported"}

    uploaded_file = Model(
        owner=request.user,
        original=f,
        original_filename=f.name,
        file_size=f.size,
        **metadata.dict(),
    )

    if not uploaded_file.title:
        # title defaults to the original filename
        uploaded_file.title = uploaded_file.original_filename

    # save everything and return
    uploaded_file.save()

    # assign permissions (publish_basefile and unpublish_basefile are assigned after moderation)
    assign_perm("view_basefile", request.user, uploaded_file)
    assign_perm("change_basefile", request.user, uploaded_file)
    assign_perm("delete_basefile", request.user, uploaded_file)

    # return response
    return 201, uploaded_file


@router.get(
    "/{file_uuid}/",
    response={200: FileOutSchema, 403: MessageSchema, 404: MessageSchema},
    summary="Return the metadata of a file.",
    auth=None,
)
def file_get(request, file_uuid: uuid.UUID):
    """Return a file object."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if basefile.status == "PUBLISHED" or request.user.has_perm(
        "view_basefile",
        basefile,
    ):
        return basefile
    else:
        return 403, {"message": "Permission denied"}


@router.get(
    "/",
    response={200: List[FileOutSchema]},
    summary="Return a list of files.",
    auth=None,
)
def file_list(request, filters: FileFilters = query):
    """Return a list of files."""
    # start out with a list of all PUBLISHED files plus whatever else the user has explicit access to
    files = BaseFile.objects.filter(status="PUBLISHED") | get_objects_for_user(
        request.user,
        "files.view_basefile",
    )
    files = files.distinct()

    if filters.albums:
        files = files.filter(albums__in=filters.albums)

    if filters.statuses:
        files = files.filter(status__in=filters.statuses)

    if filters.filetypes:
        query = Q()
        for filetype in filters.filetypes:
            # this could probably be more clever somehow
            if filetype == FileTypeChoices.picture:
                query |= Q(instance_of=Picture)
            elif filetype == FileTypeChoices.video:
                query |= Q(instance_of=Video)
            elif filetype == FileTypeChoices.audio:
                query |= Q(instance_of=Audio)
            elif filetype == FileTypeChoices.document:
                query |= Q(instance_of=Document)
        files = files.filter(query)

    if filters.owners:
        files = files.filter(owner__in=filters.owners)

    if filters.size:
        files = files.filter(file_size=filters.size)

    if filters.size_lt:
        files = files.filter(file_size__lt=filters.size_lt)

    if filters.size_gt:
        files = files.filter(file_size__gt=filters.size_gt)

    if filters.search:
        # we search title and description fields for now
        files = files.filter(title__icontains=filters.search) | files.filter(
            description__icontains=filters.search,
        )

    if filters.sorting:
        if filters.sorting.endswith("_asc"):
            # remove _asc and add +
            files = files.order_by(f"{filters.sorting[:-4]}")
        else:
            # remove _desc and add -
            files = files.order_by(f"-{filters.sorting[:-5]}")

    if filters.offset:
        files = files[filters.offset :]

    if filters.limit:
        files = files[: filters.limit]

    return files


@router.put(
    "/{file_uuid}/",
    response={
        200: FileOutSchema,
        403: MessageSchema,
        404: MessageSchema,
        422: MessageSchema,
    },
    operation_id="files_api_file_update_put",
    summary="Replace the metadata of a file.",
)
@router.patch(
    "/{file_uuid}/",
    response={
        200: FileOutSchema,
        403: MessageSchema,
        404: MessageSchema,
        422: MessageSchema,
    },
    operation_id="files_api_file_update_patch",
    summary="Update the metadata of a file.",
)
def file_update(request, file_uuid: uuid.UUID, metadata: FileUpdateSchema):
    """Update (PATCH) or replace (PUT) a file object."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("change_basefile", basefile):
        return 403, {"message": "Permission denied."}
    if request.method == "PATCH":
        # we are updating the object, we do not want defaults for absent fields
        exclude_unset = True
    else:
        # we are replacing the object, we do want defaults for absent fields
        exclude_unset = False
    for attr, value in metadata.dict(exclude_unset=exclude_unset).items():
        setattr(basefile, attr, value)
    basefile.save()
    return basefile


@router.patch(
    "/{file_uuid}/approve/",
    response={
        200: FileOutSchema,
        403: MessageSchema,
        404: MessageSchema,
        422: MessageSchema,
    },
    summary="Approve a file.",
    url_name="file_approve",
)
def file_approve(request, file_uuid: uuid.UUID):
    """Approve a file and grant publish/unpublish permissions to the owner."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("approve_basefile", basefile):
        return 403, {"message": "Permission denied."}
    # initial status is UNPUBLISHED (so the owner can decide when to publish)
    basefile.status = "UNPUBLISHED"
    basefile.save()
    assign_perm("publish_basefile", basefile.owner, basefile)
    assign_perm("unpublish_basefile", basefile.owner, basefile)
    return basefile


@router.patch(
    "/{file_uuid}/unpublish/",
    response={
        200: FileOutSchema,
        403: MessageSchema,
        404: MessageSchema,
        422: MessageSchema,
    },
    summary="Unpublish a file.",
)
def file_unpublish(request, file_uuid: uuid.UUID):
    """Change the status of a file to UNPUBLISHED."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("unpublish_basefile", basefile):
        return 403, {"message": "Permission denied."}
    basefile.status = "UNPUBLISHED"
    basefile.save()
    return basefile


@router.patch(
    "/{file_uuid}/publish/",
    response={
        200: FileOutSchema,
        403: MessageSchema,
        404: MessageSchema,
        422: MessageSchema,
    },
    summary="Publish a file.",
)
def file_publish(request, file_uuid: uuid.UUID):
    """Change the status of a file to PUBLISHED."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("publish_basefile", basefile):
        return 403, {"message": "Permission denied."}
    basefile.status = "PUBLISHED"
    basefile.save()
    return basefile


@router.delete(
    "/{file_uuid}/",
    response={204: None, 403: MessageSchema, 404: MessageSchema},
    summary="Delete a file.",
)
def file_delete(request, file_uuid: uuid.UUID):
    """Mark a file for deletion."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("delete_basefile", basefile):
        return 403, {"message": "Permission denied."}
    # we don't let users fully delete files for now
    # basefile.delete()
    basefile.status = "PENDING_DELETION"
    basefile.save()
    return 204, None
