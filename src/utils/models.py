"""This module defines the base models used in the rest of the models."""

import uuid

from django.db import models


class BaseModel(models.Model):
    """The BaseModel which all other models are based on."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        """This is an abstract class."""

        abstract = True
