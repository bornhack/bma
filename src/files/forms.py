"""The file upload form."""

from typing import ClassVar

from django import forms

from utils.filefield import MultipleFileField

from .models import BaseFile


class UploadForm(forms.ModelForm[BaseFile]):
    """The file upload form."""

    files = MultipleFileField(label="Select file(s) *")  # type: ignore[assignment]

    class Meta:
        """Set model and fields."""

        model = BaseFile
        fields = ("license", "attribution", "tags")
        labels: ClassVar[dict[str, str]] = {
            "license": "License *",
            "attribution": "Attribution *",
            "tags": "Initial tags for file(s) (optional)",
        }
        help_texts: ClassVar[dict[str, str]] = {
            "license": (
                "The Creative Commons license under which you are publishing these files. "
                "Note that CC licenses can not be revoked."
            ),
            "attribution": (
                "The attribution text for these files. This is usually the real name or "
                "handle of the photographer, author(s) or licensor of the file."
            ),
            "tags": "Your initial tags for these files. Seperate multiple tags with space.",
        }
        widgets: ClassVar[dict[str, forms.Select | forms.TextInput]] = {
            "license": forms.Select(attrs={"onchange": "enableUploadButton()"}),
            "attribution": forms.TextInput(attrs={"placeholder": "Attribution", "onchange": "enableUploadButton()"}),
            "tags": forms.TextInput(
                attrs={"placeholder": "Tags (space-seperated)", "onchange": "enableUploadButton()"}
            ),
        }


class FileMultipleActionForm(forms.Form):
    """The file action form used with the file list table."""

    action = forms.ChoiceField(
        choices=(
            ("", "----"),
            ("create_album", "Create New Album With Files"),
            ("add_to_album", "Add Files To Existing Album"),
            ("remove_from_album", "Remove Files From Existing Album"),
        )
    )

    selection = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
    )

    fromurl = forms.CharField(help_text="The URL to return to after a failed form validation.")
