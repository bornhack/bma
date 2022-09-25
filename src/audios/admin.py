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
        "original",
        "tags"
    ]
    list_filter = ["tags"]
