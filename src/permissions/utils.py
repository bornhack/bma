"""Permission related utility functions."""

from typing import TYPE_CHECKING
from typing import TypeAlias

from django.contrib.auth.models import Permission
from guardian.models import GroupObjectPermissionBase
from guardian.models import UserObjectPermissionBase

if TYPE_CHECKING:
    from django.contrib.auth.models import Group

    from albums.models import Album
    from files.models import BaseFile
    from permissions.models import GroupPermission
    from permissions.models import UserPermission
    from users.models import User

    PermObject: TypeAlias = "BaseFile | Album"


def bma_assign_user_perm(perm: str, user: "User", obj: "PermObject", creator: "User") -> "UserPermission":
    """Replacement for guardian.utils.assign_perm.

    Get content type and permissions model and assign permission.
    """
    model = get_permission_model(obj, base=UserObjectPermissionBase)
    p = Permission.objects.get(codename=perm)
    return model.objects.create(  # type: ignore[misc]
        content_object=obj,
        permission=p,
        user=user,
        created_by=creator,
    )


def bma_assign_group_perm(perm: str, group: "Group", obj: "PermObject", creator: "User") -> "GroupPermission":
    """Replacement for guardian.utils.assign_perm.

    Get content type and permissions model and assign permission.
    """
    model = get_permission_model(obj, base=GroupObjectPermissionBase)
    p = Permission.objects.get(codename=perm)
    return model.objects.create(  # type: ignore[misc]
        content_object=obj,
        permission=p,
        group=group,
        created_by=creator,
    )


def get_permission_model(
    obj: "PermObject", base: "UserObjectPermissionBase | GroupObjectPermissionBase"
) -> "UserPermission | GroupPermission":
    """Get the permission model for a given object and base class."""
    fields = (f for f in obj._meta.get_fields() if (f.one_to_many or f.one_to_one) and f.auto_created)  # noqa: SLF001
    for attr in fields:
        model = attr.related_model
        if issubclass(model, base):  # type: ignore[arg-type]
            return model  # type: ignore[return-value]
    raise ValueError("Fuck")
