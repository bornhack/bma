"""The file admin site."""

from django.contrib import admin
from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from guardian.shortcuts import get_objects_for_user

from utils.admin import file_admin

from .models import BaseFile


@admin.register(BaseFile)
class BaseFileAdmin(admin.ModelAdmin[BaseFile]):
    """The ModelAdmin class to manage files. Used by the regular admin and FileAdmin."""

    readonly_fields = (
        "original_filename",
        "file_size",
        "license",
        "uploader",
        "approved",
        "published",
        "deleted",
        "mimetype",
    )
    list_display = (
        "uuid",
        "uploader",
        "thumbnail",
        "downloads",
        "permissions",
        "mimetype",
        "created",
        "updated",
        "title",
        "license",
        "attribution",
        "approved",
        "published",
        "deleted",
    )
    list_filter = ("license", "uploader", "attribution", "approved", "published", "deleted")
    actions = ("approve", "unapprove", "publish", "unpublish", "softdelete", "undelete")
    exclude = ("tags",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[BaseFile]:
        """Only return files the user has permission to see and use the bmanager."""
        return BaseFile.bmanager.get_permitted(user=request.user)  # type: ignore[no-any-return]

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[BaseFile]) -> None:
        """Soft delete."""
        queryset.update(deleted=True)

    def has_module_permission(self, request: HttpRequest) -> bool:
        """All users may see this modules index page."""
        return True

    def has_view_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called by the admin to check if the user has permission to view this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("view_basefile", obj)

    def has_change_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called by the admin to check if the user has permission to change this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("change_basefile", obj)

    def has_delete_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called to check if the user has permission to really (non-soft) delete this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("delete_basefile", obj)

    def has_approve_basefile_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called by the admin to check if the user has permission to approve this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("approve_basefile", obj)

    def has_unapprove_basefile_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called by the admin to check if the user has permission to unapprove this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("unapprove_basefile", obj)

    def has_publish_basefile_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called by the admin to check if the user has permission to publish this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("publish_basefile", obj)

    def has_unpublish_basefile_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called by the admin to check if the user has permission to unpublish this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("unpublish_basefile", obj)

    def has_softdelete_basefile_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called by the admin to check if the user has permission to softdelete this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("softdelete_basefile", obj)

    def has_undelete_basefile_permission(self, request: HttpRequest, obj: BaseFile | None = None) -> bool:
        """Called by the admin to check if the user has permission to undelete this type of/this specific object."""
        if obj is None:
            return True
        return request.user.has_perm("undelete_basefile", obj)

    def send_message(self, request: HttpRequest, selected: int, valid: int, updated: int, action: str) -> None:
        """Return a message to the user."""
        # set status
        status = (messages.SUCCESS if updated == valid else messages.WARNING) if updated else messages.ERROR
        # send message
        self.message_user(
            request,
            f"{selected} files selected to be {action}, "
            f"out of those {valid} files had needed permission, "
            f"and out of those {updated} files were successfully {action}",
            status,
        )

    @admin.action(
        description="Approve selected %(verbose_name_plural)s",
        permissions=["approve_basefile"],
    )
    def approve(self, request: HttpRequest, queryset: QuerySet[BaseFile]) -> None:
        """Admin action to approve files."""
        selected = queryset.count()
        valid = get_objects_for_user(request.user, "files.approve_basefile", klass=queryset)
        valids = valid.count()
        updated = valid.approve()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="approved")

    @admin.action(
        description="Unapprove selected %(verbose_name_plural)s",
        permissions=["unapprove_basefile"],
    )
    def unapprove(self, request: HttpRequest, queryset: QuerySet[BaseFile]) -> None:
        """Admin action to unapprove files."""
        selected = queryset.count()
        valid = get_objects_for_user(request.user, "files.unapprove_basefile", klass=queryset)
        valids = valid.count()
        updated = valid.unapprove()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="unapproved")

    @admin.action(
        description="Publish selected %(verbose_name_plural)s",
        permissions=["publish_basefile"],
    )
    def publish(self, request: HttpRequest, queryset: QuerySet[BaseFile]) -> None:
        """Admin action to publish files."""
        selected = queryset.count()
        valid = get_objects_for_user(request.user, "files.publish_basefile", klass=queryset)
        valids = valid.count()
        updated = valid.publish()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="published")

    @admin.action(
        description="Unpublish selected %(verbose_name_plural)s",
        permissions=["unpublish_basefile"],
    )
    def unpublish(self, request: HttpRequest, queryset: QuerySet[BaseFile]) -> None:
        """Admin action to unpublish files."""
        selected = queryset.count()
        valid = get_objects_for_user(request.user, "files.unpublish_basefile", klass=queryset)
        valids = valid.count()
        updated = valid.unpublish()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="unpublished")

    @admin.action(
        description="Soft delete selected %(verbose_name_plural)s",
        permissions=["softdelete_basefile"],
    )
    def softdelete(self, request: HttpRequest, queryset: QuerySet[BaseFile]) -> None:
        """Admin action to softdelete files."""
        selected = queryset.count()
        valid = get_objects_for_user(request.user, "files.softdelete_basefile", klass=queryset)
        valids = valid.count()
        updated = valid.softdelete()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="deleted")

    @admin.action(
        description="Undelete selected %(verbose_name_plural)s",
        permissions=["undelete_basefile"],
    )
    def undelete(self, request: HttpRequest, queryset: QuerySet[BaseFile]) -> None:
        """Admin action to undelete files."""
        selected = queryset.count()
        valid = get_objects_for_user(request.user, "files.undelete_basefile", klass=queryset)
        valids = valid.count()
        updated = valid.undelete()
        self.send_message(request, selected=selected, valid=valids, updated=updated, action="undeleted")

    def permissions(self, obj: BaseFile) -> str:
        """Return all defined permissions for this object."""
        output = ""
        for perm in obj.user_permissions.all():
            output += f"user '{perm.user.username}' has perm '{perm.permission.codename}'<br>"
        for perm in obj.group_permissions.all():
            output += f"group '{perm.group}' has perm '{perm.permission.codename}'<br>"
        return mark_safe(output)  # noqa: S308

    def downloads(self, obj: BaseFile) -> str:
        """Return all download links for this object."""
        output = ""
        links = obj.resolve_links()
        if not isinstance(links["downloads"], dict):
            return ""
        for name, url in links["downloads"].items():
            output += f'<a href="{url}">{name}</a><br>'
        return mark_safe(output)  # noqa: S308

    def thumbnail(self, obj: BaseFile) -> str:
        """Return thumbnail html."""
        try:
            return mark_safe(f'<a href="{obj.original.url}"><img src = "{obj.thumbnail_url}" width = "100"></a>')  # noqa: S308
        except AttributeError:
            return ""


# register the BaseFile model in the file_admin
file_admin.register(BaseFile, BaseFileAdmin)
