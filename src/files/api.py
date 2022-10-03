import logging
import uuid
from typing import List
from typing import Union

import magic
from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.files import UploadedFile

from .models import BaseFile
from .schema import FileOutSchema
from .schema import FileUpdateSchema
from .schema import UploadMetadata
from audios.schema import AudioOutSchema
from documents.schema import DocumentOutSchema
from pictures.schema import PictureOutSchema
from utils.license import LicenseChoices
from utils.schema import MessageSchema
from videos.schema import VideoOutSchema

logger = logging.getLogger("bma")

# initialise API router
router = Router()


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
        **metadata.dict(),
    )

    if not uploaded_file.title:
        # title defaults to the original filename
        uploaded_file.title = uploaded_file.original_filename

    # XXX why doesn't django-ninja validate enums?
    if uploaded_file.license not in LicenseChoices:
        return 422, {"message": "Invalid license"}

    # save everything and return
    uploaded_file.save()
    return 201, uploaded_file


@router.get(
    "/{file_uuid}/",
    response={200: FileOutSchema, 403: MessageSchema, 404: MessageSchema},
    summary="Return the metadata of a file.",
)
def file_get(request, file_uuid: uuid.UUID):
    """Return a file object."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if (
        basefile.status == "PUBLISHED"
        or request.user == basefile.owner
        or request.user.is_superuser
    ):
        return basefile
    else:
        return 403, {"message": "File is not published"}


@router.get(
    "/",
    response={200: List[FileOutSchema]},
    summary="Return a list of all files.",
)
def file_list(request):
    """Return a list of all files."""
    if request.user.is_superuser:
        return BaseFile.objects.all()
    else:
        return BaseFile.objects.filter(status="PUBLISHED") | BaseFile.objects.filter(
            owner=request.user,
        )


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
    if request.user != basefile.owner:
        return 403, {"message": f"No permission to update file {file_uuid}"}
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


@router.delete(
    "/{file_uuid}/",
    response={204: None, 403: MessageSchema, 404: MessageSchema},
    summary="Delete a file.",
)
def file_delete(request, file_uuid: uuid.UUID):
    """Mark a file for deletion."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if basefile.owner != request.user:
        return 403, {"message": f"No permission to delete file {file_uuid}"}
    # we don't let users fully delete files for now
    basefile.status = "PENDING_DELETION"
    basefile.save()
    return 204, None
