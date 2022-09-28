from django.contrib import admin

from .models import Picture


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
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
        "small_thumbnail",
        "medium_thumbnail",
        "large_thumbnail",
        "small",
        "medium",
        "large",
        "slideshow",
        "tags"
    ]
    list_filter = ["tags"]

