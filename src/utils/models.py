"""This module defines the base models used in the rest of the models."""

import uuid

from django.db import models


class BaseModel(models.Model):
    """The BaseModel which all other non-polymorphic models are based on."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """This is an abstract class."""

        abstract = True


def NP_CASCADE(  # type: ignore[no-untyped-def]  # noqa: N802
    collector: models.deletion.Collector,
    field,  # noqa: ANN001
    sub_objs,  # noqa: ANN001
    using: str,
) -> None:
    """Workaround for django/polymorphic bug preventing CASCADE deletion from working.

    Use this instead of models.CASCADE for FKs to polymorphic models.
    Issue at https://github.com/jazzband/django-polymorphic/issues/229
    """
    if hasattr(sub_objs, "non_polymorphic"):
        return models.CASCADE(collector, field, sub_objs.non_polymorphic(), using)
    return models.CASCADE(collector, field, sub_objs, using)
