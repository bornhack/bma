"""The FileAdminSite used for creators and moderators."""

from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest


class FileAdminSite(admin.AdminSite):
    """The FileAdminSite used for creators and moderators."""

    site_header = "BMA File Admin"
    site_title = "BMA File Admin Portal"
    index_title = "Welcome to BMA YOLO File Management"

    def has_permission(self, request: HttpRequest) -> bool:
        """The FileAdminSite requires is_creator, is_moderator, or is_staff to be True on the User object."""
        return request.user.is_authenticated and any(
            [
                settings.BMA_CREATOR_GROUP_NAME in request.user.cached_groups,
                settings.BMA_MODERATOR_GROUP_NAME in request.user.cached_groups,
                request.user.is_staff,
            ]
        )


# the admin accessible to creators and moderators for file management
file_admin = FileAdminSite(name="file_admin")

# disable deleting files through the file admin for now
file_admin.disable_action("delete_selected")

# the global admin
admin.site.site_header = "BMA Global Admin"
admin.site.site_title = "BMA Global Admin Portal"
admin.site.index_title = "Welcome to BMA Global Django Admin"
