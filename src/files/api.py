import logging
from django.http import HttpResponse
from users.models import User
import uuid
from typing import List
from typing import Union

import magic
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm
from guardian.shortcuts import get_objects_for_user, get_objects_for_group
from ninja import Query
from ninja import Router
from ninja.files import UploadedFile

from .models import BaseFile
from .filters import FileFilters
from .schema import SingleFileResponseSchema
from .schema import MultipleFileResponseSchema
from .schema import FileTypeChoices
from .schema import FileUpdateRequestSchema
from .schema import UploadRequestSchema
from .schema import MultipleFileRequestSchema
from audios.models import Audio
from audios.schema import AudioOutSchema
from documents.models import Document
from documents.schema import DocumentOutSchema
from pictures.models import Picture
from pictures.schema import PictureOutSchema
from utils.schema import ApiMessageSchema
from files.schema import SingleFileResponseSchema
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
        201: SingleFileResponseSchema,
        403: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    summary="Upload a new file.",
)
def upload(request, f: UploadedFile, metadata: UploadRequestSchema):
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

    if not uploaded_file.thumbnail_url:
        # thumbnail url was not specified, use the default for the filetype
        uploaded_file.thumbnail_url = settings.DEFAULT_THUMBNAIL_URLS[
            uploaded_file.filetype
        ]

    try:
        uploaded_file.full_clean()
    except ValidationError:
        return 422, {"message": "Validation error"}

    # save everything
    uploaded_file.save()

    # if the filetype is picture then use the picture itself as thumbnail,
    # this has to be done after .save() to ensure the uuid filename and
    # full path is passed to the imagekit namer
    if (
        uploaded_file.filetype == "picture"
        and uploaded_file.thumbnail_url == settings.DEFAULT_THUMBNAIL_URLS["picture"]
    ):
        # use the large_thumbnail size as default
        uploaded_file.thumbnail_url = uploaded_file.large_thumbnail.url
        uploaded_file.save()

    # assign permissions (publish_basefile and unpublish_basefile are assigned after moderation)
    assign_perm("view_basefile", request.user, uploaded_file)
    assign_perm("change_basefile", request.user, uploaded_file)
    assign_perm("delete_basefile", request.user, uploaded_file)

    return 201, uploaded_file


@router.patch(
    "/approve/",
    response={
        200: MultipleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Approve multiple files (change status from PENDING_MODERATION to UNPUBLISHED).",
)
def file_approve_multiple(request, data: MultipleFileRequestSchema, check: bool = None):
    """Change the status of files PENDING_MODERATION to UNPUBLISHED."""
    files = data.dict()["files"]
    allfiles = BaseFile.objects.filter(uuid__in=files)
    dbfiles = get_objects_for_user(
        request.user,
        "approve_basefile",
        klass=BaseFile.objects.filter(
            uuid__in=[str(u) for u in files],
            status="PENDING_MODERATION",
        ),
    )
    # we want all files to have the right status and the user to have approve_basefile permissions for all files
    if dbfiles.count() < len(files):
        return 403, {
            "message": f"Wrong status or no permission to approve these {allfiles.difference(dbfiles).count()} files (of total {len(files)} files)",
            "details": {"files": [f.uuid for f in allfiles.difference(dbfiles)]},
        }
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    else:
        # not check mode, do the thing
        for basefile in dbfiles:
            # use .update() to avoid race conditions
            BaseFile.objects.filter(uuid=basefile.uuid).update(
                status="UNPUBLISHED",
                updated=timezone.now(),
            )
            assign_perm("publish_basefile", basefile.owner, basefile)
            assign_perm("unpublish_basefile", basefile.owner, basefile)
        # return the response
        if request.htmx:
            return HttpResponse(
                """<button class="btn btn-success" data-bs-dismiss="modal"><i class="fas fa-check"></i> Close</button>""",
            )
        else:
            return BaseFile.objects.filter(
                uuid__in=dbfiles.values_list("uuid", flat=True),
            )


@router.patch(
    "/publish/",
    response={
        200: MultipleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Publish multiple files (change status from UNPUBLISHED to PUBLISHED).",
)
def file_publish_multiple(request, data: MultipleFileRequestSchema, check: bool = None):
    """Change the status of files from UNPUBLISHED to PUBLISHED."""
    files = data.dict()["files"]
    allfiles = BaseFile.objects.filter(uuid__in=files)
    dbfiles = get_objects_for_user(
        request.user,
        "publish_basefile",
        klass=BaseFile.objects.filter(
            uuid__in=[str(u) for u in files],
            status="UNPUBLISHED",
        ),
    )
    # we want all files to have the right status and the user to have publish_basefile permissions for all files
    if dbfiles.count() < len(files):
        return 403, {
            "message": f"Wrong status or no permission to publish these {allfiles.difference(dbfiles).count()} files (of total {len(files)} files)",
            "details": {"files": [f.uuid for f in allfiles.difference(dbfiles)]},
        }
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    else:
        # not check mode, do the thing
        for basefile in dbfiles:
            # use .update() to avoid race conditions
            BaseFile.objects.filter(uuid=basefile.uuid).update(
                status="PUBLISHED",
                updated=timezone.now(),
            )
        # assign view_basefile permission to the anonymous user for all published files
        assign_perm("view_basefile", User.get_anonymous(), dbfiles)
        # return the response
        if request.htmx:
            return HttpResponse(
                """<button class="btn btn-success" data-bs-dismiss="modal"><i class="fas fa-check"></i> Close</button>""",
            )
        else:
            return BaseFile.objects.filter(
                uuid__in=dbfiles.values_list("uuid", flat=True),
            )


@router.patch(
    "/unpublish/",
    response={
        200: MultipleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
    },
    summary="Unpublish multiple files (change status from PUBLISHED to UNPUBLISHED).",
)
def file_unpublish_multiple(request, data: MultipleFileRequestSchema, check: bool = None):
    """Change the status of files from PUBLISHED to UNPUBLISHED."""
    files = data.dict()["files"]
    allfiles = BaseFile.objects.filter(uuid__in=files)
    dbfiles = get_objects_for_user(
        request.user,
        "unpublish_basefile",
        klass=BaseFile.objects.filter(
            uuid__in=[str(u) for u in files],
            status="PUBLISHED",
        ),
    )
    # we want all files to have the right status and the user to have approve_basefile permissions for all files
    if dbfiles.count() < len(files):
        return 403, {
            "message": f"Wrong status or no permission to unpublish these {allfiles.difference(dbfiles).count()} files (of total {len(files)} files)",
            "details": {"files": [f.uuid for f in allfiles.difference(dbfiles)]},
        }
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    else:
        # not check mode, do the thing
        for basefile in dbfiles:
            # use .update() to avoid race conditions
            BaseFile.objects.filter(uuid=basefile.uuid).update(
                status="UNPUBLISHED",
                updated=timezone.now(),
            )
        # remove view_basefile permission from the anonymous user for all unpublished files
        remove_perm("view_basefile", User.get_anonymous(), dbfiles)
        # return the response
        if request.htmx:
            return HttpResponse(
                """<button class="btn btn-success" data-bs-dismiss="modal"><i class="fas fa-check"></i> Close</button>""",
            )
        else:
            return BaseFile.objects.filter(
                uuid__in=dbfiles.values_list("uuid", flat=True),
            )


@router.patch(
    "/{file_uuid}/approve/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    summary="Approve a file (change status from PENDING_MODERATION to UNPUBLISHED).",
    url_name="file_approve",
)
def file_approve(request, file_uuid: uuid.UUID, check: bool = None):
    """Approve a file and grant publish/unpublish permissions to the owner."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("approve_basefile", basefile):
        return 403, {"message": "Permission denied."}
    if not basefile.status == "PENDING_MODERATION":
        return 403, {"message": f"Wrong status: {basefile.status}."}
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    else:
        # initial status is UNPUBLISHED (so the owner can decide when to publish)
        # use .update() to avoid race conditions
        BaseFile.objects.filter(uuid=basefile.uuid).update(
            status="UNPUBLISHED",
            updated=timezone.now(),
        )
        assign_perm("publish_basefile", basefile.owner, basefile)
        assign_perm("unpublish_basefile", basefile.owner, basefile)
        basefile.refresh_from_db()
        return basefile


@router.patch(
    "/{file_uuid}/unpublish/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    summary="Unpublish a file (change status from PUBLISHED to UNPUBLISHED).",
)
def file_unpublish(request, file_uuid: uuid.UUID, check: bool = None):
    """Change the status of a file to UNPUBLISHED."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("unpublish_basefile", basefile):
        return 403, {"message": "Permission denied."}
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    else:
        BaseFile.objects.filter(uuid=basefile.uuid).update(
            status="UNPUBLISHED",
            updated=timezone.now(),
        )
        basefile.refresh_from_db()
        # remove view_basefile permission from the anonymous user
        remove_perm("view_basefile", User.get_anonymous(), basefile)
        return basefile


@router.patch(
    "/{file_uuid}/publish/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    summary="Publish a file (change status from UNPUBLISHED to PUBLISHED).",
)
def file_publish(request, file_uuid: uuid.UUID, check: bool = None):
    """Change the status of a file to PUBLISHED."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("publish_basefile", basefile):
        return 403, {"message": "Permission denied."}
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    else:
        BaseFile.objects.filter(uuid=basefile.uuid).update(
            status="PUBLISHED",
            updated=timezone.now(),
        )
        basefile.refresh_from_db()
        # assign view_basefile permission to the anonymous user
        assign_perm("view_basefile", User.get_anonymous(), basefile)
        return basefile

@router.get(
    "/{file_uuid}/",
    response={
        200: SingleFileResponseSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
    },
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
        # https://github.com/vitalik/django-ninja/issues/610
        #return 200, {"bma_response": basefile}
        return HttpResponse(SingleFileResponseSchema.from_orm({"bma_response": basefile}).json(), content_type="application/json")
    else:
        return 403, {"message": "Permission denied."}


@router.get(
    "/",
    response={200: MultipleFileResponseSchema},
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

    if filters.licenses:
        files = files.filter(license__in=filters.licenses)

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

    return {"bma_response": list(files)}


@router.put(
    "/{file_uuid}/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    operation_id="files_api_file_update_put",
    summary="Replace the metadata of a file.",
)
@router.patch(
    "/{file_uuid}/",
    response={
        200: SingleFileResponseSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        422: ApiMessageSchema,
    },
    operation_id="files_api_file_update_patch",
    summary="Update the metadata of a file.",
)
def file_update(
    request,
    file_uuid: uuid.UUID,
    metadata: FileUpdateRequestSchema,
    check: bool = None,
):
    """Update (PATCH) or replace (PUT) a file object."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("change_basefile", basefile):
        return 403, {"message": "Permission denied."}
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    if request.method == "PATCH":
        try:
            with transaction.atomic():
                # we are updating the object, we do not want defaults for absent fields
                BaseFile.objects.filter(uuid=basefile.uuid).update(
                    **metadata.dict(exclude_unset=True), updated=timezone.now()
                )
                basefile.refresh_from_db()
                basefile.full_clean()
        except ValidationError:
            return 422, {"message": "Validation error"}
    else:
        try:
            with transaction.atomic():
                # we are replacing the object, we do want defaults for absent fields
                BaseFile.objects.filter(uuid=basefile.uuid).update(
                    **metadata.dict(exclude_unset=False), updated=timezone.now()
                )
                basefile.refresh_from_db()
                basefile.full_clean()
        except ValidationError:
            return 422, {"message": "Validation error"}
    return basefile


@router.delete(
    "/{file_uuid}/",
    response={
        204: None,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
    },
    summary="Delete a file (change status to PENDING_DELETION).",
)
def file_delete(request, file_uuid: uuid.UUID, check: bool = None):
    """Mark a file for deletion."""
    basefile = get_object_or_404(BaseFile, uuid=file_uuid)
    if not request.user.has_perm("delete_basefile", basefile):
        return 403, {"message": "Permission denied."}
    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}
    else:
        # we don't let users fully delete files for now
        # basefile.delete()
        basefile.status = "PENDING_DELETION"
        basefile.save()
        return 204, None



