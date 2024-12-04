"""The jobs API."""

import json
import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Query
from ninja import Router
from ninja.files import UploadedFile

from files.models import BaseFile
from files.models import LicenseChoices
from files.models import license_urls
from files.schema import ImageMetadataSchema
from files.schema import SingleFileResponseSchema
from jobs.models import BaseJob
from jobs.schema import JobClientSchema
from jobs.schema import MultipleJobResponseSchema
from jobs.schema import SettingsResponseSchema
from utils.api import FileApiResponseType
from utils.api import JobApiResponseType
from utils.api import JobSettingsResponseType
from utils.auth import BMAuthBearer
from utils.auth import permit_anonymous_api_use
from utils.schema import ApiMessageSchema

from .filters import JobFilters

logger = logging.getLogger("bma")

# initialise API router
router = Router()
query: Query = Query(...)  # type: ignore[type-arg]


@router.get(
    "/settings/",
    response={
        200: SettingsResponseSchema,
    },
    summary="Return the client-relevant settings active on the BMA server.",
)
def job_settings(request: HttpRequest) -> JobSettingsResponseType:
    """API endpoint for returning the settings of the BMA server."""
    response = {
        "filetypes": {
            "image": dict(settings.ALLOWED_IMAGE_TYPES),
            "video": dict(settings.ALLOWED_VIDEO_TYPES),
            "audio": dict(settings.ALLOWED_AUDIO_TYPES),
            "document": dict(settings.ALLOWED_DOCUMENT_TYPES),
        },
        "licenses": {k: {"title": v, "url": license_urls[k]} for k, v in dict(LicenseChoices.choices).items()},
        "encoding": {
            "images": settings.IMAGE_ENCODING,
        },
    }
    return 200, {"bma_response": response}


def filter_jobs(jobs: QuerySet[BaseJob], filters: JobFilters) -> QuerySet[BaseJob]:
    """Apply filters and return filtered jobs."""
    if filters.file_uuid:
        jobs = jobs.filter(basefile__uuid=filters.file_uuid)

    if filters.user_uuid:
        jobs = jobs.filter(user__uuid=filters.user_uuid)

    if filters.client_uuid:
        jobs = jobs.filter(client_uuid=filters.client_uuid)

    if filters.client_version:
        jobs = jobs.filter(client_version=filters.client_version)

    if filters.finished is not None:
        jobs = jobs.filter(finished=filters.finished)

    if filters.skip_jobs:
        jobs = jobs.exclude(uuid__in=filters.skip_jobs)

    return jobs


@router.get(
    "/",
    response={
        200: MultipleJobResponseSchema,
        404: ApiMessageSchema,
    },
    summary="Return a list of jobs this user has permission to do.",
    auth=[BMAuthBearer(), permit_anonymous_api_use],
)
def job_list(request: HttpRequest, filters: JobFilters = query) -> JobApiResponseType:
    """API endpoint for listing jobs the user has permission to do."""
    # filter jobs and return
    jobs = filter_jobs(jobs=BaseJob.objects.all(), filters=filters)
    if filters.offset:
        jobs = jobs[filters.offset :]
    if filters.limit:
        jobs = jobs[: filters.limit]
    logger.debug(f"Returning {jobs.count()} jobs")
    return 200, {"bma_response": jobs, "message": f"Returning {jobs.count()} jobs"}


@router.post(
    "/assign/",
    response={
        200: MultipleJobResponseSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        500: ApiMessageSchema,
    },
    summary="Assign jobs for a file to the calling user.",
)
def assign_file_jobs(
    request: HttpRequest, client: JobClientSchema, filters: JobFilters = query, *, check: bool = False
) -> JobApiResponseType:
    """Assign jobs for a file to the calling user."""
    if not request.user.is_worker:  # type: ignore[union-attr]
        return 403, {"message": "No worker permission."}

    # clear old assigned unfinished jobs here
    BaseJob.objects.filter(
        finished=False, user__isnull=False, updated_at__lt=timezone.now() - timedelta(hours=24)
    ).update(user=None, client_uuid=None, client_version="")
    # get all jobs
    jobs = filter_jobs(jobs=BaseJob.objects.all(), filters=filters)

    # ignore finished jobs and assigned jobs
    jobs = jobs.filter(
        finished=False,
        user__isnull=True,
    )
    if not jobs.exists() or jobs is None:
        return 404, {"message": "No unassigned and unfinished jobs jobs found. Nothing to do right now."}

    # pick a file and get all other jobs for the same file
    file_uuid = jobs.values_list("basefile_id", flat=True)[0]
    jobs = jobs.filter(
        basefile__pk=file_uuid,
        finished=False,
        user__isnull=True,
    )
    if not jobs.exists():
        # race condition, another client was just assigned/just finished this job
        return 500, {"message": "Concurrency issue, please try again. PRs welcome."}

    # assign and return jobs
    job_ids = list(jobs.values_list("uuid", flat=True))
    logger.debug(f"Assigning {jobs.count()} jobs for file {file_uuid} to user {request.user}: {job_ids}")
    jobs.update(user=request.user, client_uuid=client.client_uuid, client_version=client.client_version)
    # reload from db
    jobs = BaseJob.objects.filter(uuid__in=job_ids)
    return 200, {"bma_response": jobs, "message": f"Assigned {jobs.count()} jobs"}


@router.post(
    "/{job_uuid}/result/",
    response={
        200: SingleFileResponseSchema,
        404: ApiMessageSchema,
        422: ApiMessageSchema,
        500: ApiMessageSchema,
    },
    summary="Upload the result of a job",
)
def upload_result(  # noqa: PLR0913
    request: HttpRequest,
    *,
    job_uuid: uuid.UUID,
    f: UploadedFile,
    client: JobClientSchema,
    metadata: ImageMetadataSchema | None = None,
    check: bool = False,
) -> FileApiResponseType:
    """Endpoint for uploading the result of a job."""
    if not request.user.is_worker:  # type: ignore[union-attr]
        return 403, {"message": "No worker permission."}

    # get job and file
    job = get_object_or_404(BaseJob, uuid=job_uuid, finished=False)
    basefile = job.basefile

    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}

    try:
        # process and save ImageConversionJob result
        if job.job_type in ["ImageConversionJob", "ThumbnailJob", "ThumbnailSourceJob"]:
            if metadata is None:
                return 422, {"message": "Result validation error"}
            data = metadata.dict()
            job.handle_result(f=f, data=data)

        # save exif data from ImageExifExtractionJob
        elif job.job_type == "ImageExifExtractionJob":
            exif = json.load(f)
            basefile.exif = exif
            basefile.save(update_fields=["exif", "updated_at"])

        else:
            logger.debug(f"Unsupported job type: {job.job_type}")
            return 422, {"message": "Unsupported job type"}
    except ValidationError:
        logger.exception("Result validation error")
        return 422, {"message": "Result validation error"}

    # mark job as completed
    job.user = request.user
    job.client_uuid = client.client_uuid
    job.client_version = client.client_version
    job.finished = True
    job.save(update_fields=["user", "client_uuid", "client_version", "finished", "updated_at"])

    # refresh basefile to get updated jobcount,
    # use bmanager to get annotated file object
    basefile = BaseFile.bmanager.get(uuid=basefile.uuid)
    return 200, {"bma_response": basefile}


@router.post(
    "/{job_uuid}/unassign/",
    response={
        200: ApiMessageSchema,
        202: ApiMessageSchema,
        403: ApiMessageSchema,
        404: ApiMessageSchema,
        500: ApiMessageSchema,
    },
    summary="Unassign a job from a client",
)
def unassign_job(
    request: HttpRequest,
    job_uuid: uuid.UUID,
    *,
    check: bool = False,
) -> ApiMessageSchema | tuple[int, dict[str, str]]:
    """Endpoint for unassigning a job from a client/user."""
    if not request.user.is_worker:  # type: ignore[union-attr]
        return 403, {"message": "No worker permission."}

    # get job and file
    job = get_object_or_404(BaseJob, uuid=job_uuid, finished=False)

    if check:
        # check mode requested, don't change anything
        return 202, {"message": "OK"}

    # mark job as completed
    job.user = None
    job.client_uuid = None
    job.client_version = ""
    job.save(update_fields=["user", "client_uuid", "client_version", "updated_at"])

    return 200, {"message": "OK, job unassigned"}
