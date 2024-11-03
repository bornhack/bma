"""Admin module for the tags app."""

from django.contrib import admin

from .models import TaggedFile


@admin.register(TaggedFile)
class TaggedFileAdmin(admin.ModelAdmin[TaggedFile]):
    """The ModelAdmin class to manage file<>user<>tag relations."""

    list_display = (
        "pk",
        "tag",
        "content_object",
        "tagger",
    )
