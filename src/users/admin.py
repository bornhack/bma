"""ModelAdmin for the User model."""

from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin[User]):
    """ModelAdmin for the User model."""

    list_display = ("username", "handle", "display_name", "description")
    list_filter = ("username", "handle", "display_name")
    search_fields = ("username", "handle", "display_name", "description")
