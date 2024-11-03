"""Multi-file form fields.

This code is all borrowed from https://docs.djangoproject.com/en/5.0/topics/http/file-uploads/#id5
"""

from typing import Any

from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    """CLearableFileInput which allows multiple files to be selected."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """FileField which uses MultipleFileInput and supports multiple files."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Change default widget."""
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data: Any, initial: Any = None) -> Any:  # noqa: ANN401
        """Clean one or multiple files."""
        single_file_clean = super().clean
        if isinstance(data, list | tuple):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result
