from django.contrib import admin

from .models import BaseFile


@admin.register(BaseFile)
class BaseFileAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "owner",
        "created",
        "updated",
        "title",
        "license",
        "attribution",
        "status",
    ]
    list_filter = ["license", "status"]
