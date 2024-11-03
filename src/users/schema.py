"""Response schemas for representing users."""

import datetime
import uuid

from ninja import ModelSchema

from .models import User


class UserResponseSchema(ModelSchema):
    """Schema used for responses including a user object."""

    uuid: uuid.UUID
    handle: str
    display_name: str
    description: str = ""
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        """Specify the model fields to include."""

        model = User
        model_fields = (
            "uuid",
            "handle",
            "display_name",
            "description",
            "created_at",
            "updated_at",
        )
