from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
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
        "tags",
    ]
    list_filter = ["tags"]
