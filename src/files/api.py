import logging
from typing import Union

import magic
from django.conf import settings
from django.shortcuts import render
from ninja import Router
from ninja.files import UploadedFile
from ninja.security import django_auth

from .schema import UploadMetadata
from audios.schema import AudioOutSchema
from documents.schema import DocumentOutSchema
from pictures.schema import PictureOutSchema
from utils.license import LicenseChoices
from utils.schema import Message
from videos.schema import VideoOutSchema

logger = logging.getLogger("bma")

# initialise API router
router = Router()


@router.post(
    "/upload/",
    auth=django_auth,
    response={
        200: Union[PictureOutSchema, VideoOutSchema, AudioOutSchema, DocumentOutSchema],
        400: Message,
    },
)
def upload(request, f: UploadedFile, metadata: UploadMetadata):
    """This API endpoint is used for all file uploads (from HTMX or other API clients)."""
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
        return 400, {"message": "File type not supported"}

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
        return 400, {"message": "Invalid license"}

    # save everything
    uploaded_file.save()

    if request.htmx:
        # htmx request, return html
        return render(request, "htmx/upload_ok.html", uploaded_file)
    else:
        # not htmx, return json
        return uploaded_file
