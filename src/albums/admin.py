from django.contrib import admin

from .models import Album


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "owner",
        "created",
        "updated",
        "title",
        "description",
        "tags",
    ]
    list_filter = ["owner"]
