"""The file upload form."""
from django import forms
from utils.filefield import MultipleFileField

from .models import BaseFile


class UploadForm(forms.ModelForm[BaseFile]):
    """The file upload form."""

    files = MultipleFileField()  # type: ignore[assignment]

    class Meta:
        """Set model and fields."""

        model = BaseFile
        fields = ("license", "attribution")


class UpdateForm(forms.ModelForm[BaseFile]):
    """The file update form."""

    class Meta:
        """Set model and fields."""

        model = BaseFile
        fields = ("title", "attribution", "description")
