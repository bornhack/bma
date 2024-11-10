"""Filters used in django-ninja jobs endpoints."""

import uuid

from ninja import Schema


class JobFilters(Schema):
    """Filters for the job_list endpoint."""

    limit: int = 100
    offset: int | None = None
    file_uuid: uuid.UUID | None = None
    user_uuid: uuid.UUID | None = None
    client_uuid: uuid.UUID | None = None
    client_version: str | None = None
    finished: bool | None = None
