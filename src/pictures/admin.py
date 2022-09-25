from django.contrib import admin

from .models import Picture


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = [
        "gallery",
        "uuid",
        "created",
        "updated",
        "title",
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

