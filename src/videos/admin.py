from django.contrib import admin

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        "gallery",
        "uuid",
        "created",
        "updated",
        "title",
        "description",
        "source",
        "status",
        "original_filename",
        "original",
        "tags"
    ]
    list_filter = ["tags"]

