"""Permission related models."""

from typing import TYPE_CHECKING
from typing import TypeAlias

from django.db import models

from users.sentinel import get_deleted_user
from utils.models import BaseModel

if TYPE_CHECKING:
    from albums.models import AlbumGroupPermission
    from albums.models import AlbumUserPermission
    from files.models import FileGroupPermission
    from files.models import FileUserPermission


class PermissionModelBase(BaseModel):
    """Base model for the user and group models used by guardian."""

    created_by = models.ForeignKey(
        "users.User",
        related_name="%(app_label)s_%(class)s_permissions",
        on_delete=models.SET(get_deleted_user),
    )

    class Meta:
        """This is an abstract model."""

        abstract = True


UserPermission: TypeAlias = "FileUserPermission | AlbumUserPermission"
GroupPermission: TypeAlias = "FileGroupPermission | AlbumGroupPermission"
Permission: TypeAlias = "UserPermission | GroupPermission"
