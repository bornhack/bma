from django.contrib import admin

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        "original",
        "tags"
    ]
    list_filter = ["tags"]

