import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_credit_name = models.CharField(
        max_length=100,
        default="Unnamed user",
        help_text="The public_credit_name field of the user profile on the BornHack website.",
    )
    description = models.TextField(
        help_text="The description field of the user profile on the BornHack website.",
    )
