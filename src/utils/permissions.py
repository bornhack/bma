"""Permission related functions."""

import logging

from django.db.models import QuerySet
from django.http import HttpRequest
from guardian.models import GroupObjectPermission
from guardian.models import UserObjectPermission
from guardian.shortcuts import get_group_perms
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_user_perms

from albums.models import Album
from files.models import BaseFile
from utils.schema import ObjectPermissionSchema

logger = logging.getLogger("bma")


def get_object_permissions_schema(obj: BaseFile | Album, request: HttpRequest) -> ObjectPermissionSchema:
    """Get user and group permissions for a user and object."""
    user = request.user
    # get user perms
    user_perms = list(get_user_perms(user, obj))
    user_perms.sort()
    # get group perms
    group_perms = list(get_group_perms(user, obj))
    group_perms.sort()
    # get effective perms (combined user and group perms for the user)
    effective_perms = list(get_perms(user, obj))
    effective_perms.sort()
    # populate and return the schema
    return ObjectPermissionSchema(
        user_permissions=user_perms,
        group_permissions=group_perms,
        effective_permissions=effective_perms,
    )


def get_all_user_object_permissions(obj: BaseFile | Album) -> QuerySet[UserObjectPermission]:
    """Return all user permissions for a file or album."""
    return UserObjectPermission.objects.filter(object_pk=obj.pk)  # type: ignore[no-any-return]


def get_all_group_object_permissions(obj: BaseFile | Album) -> QuerySet[GroupObjectPermission]:
    """Return all group permissions for a file or album."""
    return GroupObjectPermission.objects.filter(object_pk=obj.pk)  # type: ignore[no-any-return]
