"""The file upload form."""
from django import forms
from utils.filefield import MultipleFileField

from .models import BaseFile


class UploadForm(forms.ModelForm[BaseFile]):
    """The file upload form."""

    files = MultipleFileField(label="Select file(s) *")  # type: ignore[assignment]

    class Meta:
        """Set model and fields."""

        model = BaseFile
        fields = ("license", "attribution")
        labels = {
            "license": "License *",
            "attribution": "Attribution *",
        }
        widgets = {
            "license": forms.Select(attrs={"onchange": "enableUploadButton()"}),
            "attribution": forms.TextInput(attrs={"placeholder": "Attribution",
                                                  "onchange": "enableUploadButton()"}),
        }
