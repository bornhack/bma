"""Response schemas for file processing jobs."""

import uuid

from django.http import HttpRequest
from ninja import Schema

from utils.schema import ApiResponseSchema

from .models import BaseJob
from .models import ImageConversionJob


class JobRequestSchema(Schema):
    """The schema used for requests for job assignment or job result submission."""

    client_uuid: uuid.UUID


class JobResponseSchema(Schema):
    """Base schema for representing an image conversion job in a response."""

    basefile_uuid: uuid.UUID
    client_uuid: uuid.UUID | None = None
    finished: bool
    job_type: str
    job_uuid: uuid.UUID
    user_uuid: uuid.UUID | None = None
    useragent: str | None = None

    @staticmethod
    def resolve_job_uuid(obj: BaseJob, context: dict[str, HttpRequest]) -> uuid.UUID:
        """Get the value for the job_uuid field."""
        return obj.uuid  # type: ignore[no-any-return]

    @staticmethod
    def resolve_basefile_uuid(obj: ImageConversionJob, context: dict[str, HttpRequest]) -> uuid.UUID:
        """Get the value for the basefile_uuid field."""
        if isinstance(obj, dict) and "basefile_uuid" in obj:
            return obj["basefile_uuid"]  # type: ignore[no-any-return]
        return obj.basefile_id  # type: ignore[no-any-return]

    @staticmethod
    def resolve_user_uuid(obj: BaseJob, context: dict[str, HttpRequest]) -> uuid.UUID:
        """Get the value for the user_uuid field."""
        return obj.user_id  # type: ignore[no-any-return]


class ImageConversionJobResponseSchema(JobResponseSchema):
    """Schema used for representing an image conversion job in a response."""

    filetype: str
    mimetype: str
    width: int
    height: int
    custom_aspect_ratio: bool


class ExifExtractionJobResponseSchema(JobResponseSchema):
    """Schema used for representing an exif metadata extraction job in a response."""

    # this job schema has no extra fields


class SingleJobResponseSchema(ApiResponseSchema):
    """The schema used to return a response with a single job object."""

    bma_response: ImageConversionJobResponseSchema | ExifExtractionJobResponseSchema


class MultipleJobResponseSchema(ApiResponseSchema):
    """The schema used to return a response with multiple job objects."""

    # IMPORTANT; ENTIRE DAY WASTED HERE:
    # django-ninja picks the first schema in this union which the object
    # has values to satisfy all fields. Put the schema with fewest fields last. Sigh.
    bma_response: list[ImageConversionJobResponseSchema | ExifExtractionJobResponseSchema]


##################### SETTINGS ##################################


class SettingsSchema(Schema):
    """The schema used to represent settings in responses."""

    filetypes: dict[str, dict[str, str]]
    licenses: dict[str, str]


class SettingsResponseSchema(Schema):
    """The schema used to return a response with a single settings object."""

    bma_response: SettingsSchema
