from django.contrib import admin

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "owner",
        "created",
        "updated",
        "title",
        "description",
        "source",
        "license",
        "attribution",
        "status",
        "original_filename",
        "original",
    ]
    list_filter = ["tags"]
