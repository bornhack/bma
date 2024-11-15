"""This module defines the base models used in the rest of the models."""

import uuid
from typing import TYPE_CHECKING

from django.db import models
from pictures.models import PictureField

if TYPE_CHECKING:
    from images.models import Image


class BaseModel(models.Model):
    """The BaseModel which all other non-polymorphic models are based on."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        """This is an abstract class."""

        abstract = True


class NoPillowPictureField(PictureField):
    """A subclass of django-pictures PictureField which doesn't invoke pillow."""

    def update_dimension_fields(self, instance: "Image", force: bool = False, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN002,ANN003,FBT001,FBT002
        """Do nothing method to avoid reading the image dimensions using PIL."""
