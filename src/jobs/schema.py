"""Response schemas for file processing jobs."""

import uuid
from typing import TypeAlias

from django.http import HttpRequest
from ninja import Schema

from utils.schema import ApiResponseSchema

from .models import BaseJob
from .models import ImageConversionJob

################### REQUEST SCHEMAS ########################


class JobClientSchema(Schema):
    """The client metadata schema used for requests for job assignment and for job result submission."""

    client_uuid: uuid.UUID
    client_version: str


################### RESPONSE SCHEMAS ########################


class JobResponseSchema(Schema):
    """Base schema for representing a job in a response. Inherited by other schemas."""

    schema_name: str
    basefile_uuid: uuid.UUID
    client_uuid: uuid.UUID | None = None
    client_version: str | None = None
    finished: bool
    job_type: str
    job_uuid: uuid.UUID
    user_uuid: uuid.UUID | None = None
    source_url: str
    source_filename: str

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

    @staticmethod
    def resolve_source_url(obj: BaseJob, context: dict[str, HttpRequest]) -> str:
        """Get the value for the source_url field."""
        return obj.source_url


class ImageConversionJobResponseSchema(JobResponseSchema):
    """Schema used for representing an image conversion job in a response."""

    schema_name: str = "ImageConversionJobResponseSchema"
    filetype: str
    mimetype: str
    width: int
    height: int
    custom_aspect_ratio: bool


class ExifExtractionJobResponseSchema(JobResponseSchema):
    """Schema used for representing an exif metadata extraction job in a response."""

    # this job schema has no extra fields
    schema_name: str = "ExifExtractionJobResponseSchema"


class ThumbnailSourceJobResponseSchema(JobResponseSchema):
    """Schema used for representing a thumbnail source job in a response."""

    # this job schema has no extra fields
    schema_name: str = "ThumbnailSourceJobResponseSchema"


class ThumbnailJobResponseSchema(JobResponseSchema):
    """Schema used for representing a thumbnail job in a response."""

    # this job schema has no extra fields
    schema_name: str = "ThumbnailJobResponseSchema"


# IMPORTANT; ENTIRE DAY WASTED HERE:
# django-ninja picks the first schema in this union which the object
# has values to satisfy all fields, without raising an exception.
# Put the schema with fewest fields last. Sigh.
Job: TypeAlias = (
    ImageConversionJobResponseSchema
    | ExifExtractionJobResponseSchema
    | ThumbnailSourceJobResponseSchema
    | ThumbnailJobResponseSchema
)


class SingleJobResponseSchema(ApiResponseSchema):
    """The schema used to return a response with a single job object."""

    bma_response: Job


class MultipleJobResponseSchema(ApiResponseSchema):
    """The schema used to return a response with multiple job objects."""

    bma_response: list[Job]


##################### SETTINGS ##################################


class SettingsSchema(Schema):
    """The schema used to represent settings in responses."""

    filetypes: dict[str, dict[str, str]]
    licenses: dict[str, str]
    encoding: dict[str, dict[str, dict[str, bool | float]]]


class SettingsResponseSchema(Schema):
    """The schema used to return a response with a single settings object."""

    bma_response: SettingsSchema
