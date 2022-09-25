from django.contrib import admin

from .models import Audio


@admin.register(Audio)
class AudioAdmin(admin.ModelAdmin):
    list_display = [
        "original",
        "tags"
    ]
    list_filter = ["tags"]
