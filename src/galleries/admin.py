from django.contrib import admin

from .models import Gallery


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "owner",
        "name",
        "description",
        "tags",
        "license",
        "attribution",
        "status",
    ]
    list_filter = ["owner", "license", "status"]
