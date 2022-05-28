from django.conf import settings
from django.db import models
from taggit.managers import TaggableManager

from utils.models import BaseModel
from utils.models import UUIDTaggedItem


class Gallery(BaseModel):
    """The Gallery class is used for grouping uploaded files."""

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="uploaded_%(class)s",
        help_text="The photographer / copyright holder for this file.",
    )

    name = models.CharField(
        max_length=100,
        help_text="The name of this gallery. Keep it under 100 characters please.",
    )

    slug = models.SlugField(
        help_text="The URL slug for this gallery. Leave blank to generate based on name.",
    )

    tags = TaggableManager(through=UUIDTaggedItem)

    license = models.CharField(
        max_length=20,
        choices=settings.LICENSES,
        help_text="The license for files in this gallery.",
    )

    attribution = models.CharField(
        max_length=255,
        help_text="The attribution text for files in this gallery. This is usually the real name of the creator/copyright holder.",
    )

    published = models.BooleanField(
        default=True,
        help_text="Is the gallery published on the website or not.",
    )
