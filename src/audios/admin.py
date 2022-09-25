from django.contrib import admin

from .models import Audio


@admin.register(Audio)
class AudioAdmin(admin.ModelAdmin):
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
