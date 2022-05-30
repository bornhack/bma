from django import forms
from django.conf import settings

from .models import Gallery


class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ["name", "tags", "license", "attribution"]

    # files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))
    files = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "multiple": True,
                "accept": ",".join(settings.ALLOWED_PHOTO_TYPES.keys())
                + ",".join(settings.ALLOWED_VIDEO_TYPES.keys())
                + ",".join(settings.ALLOWED_AUDIO_TYPES.keys())
                + ",".join(settings.ALLOWED_DOCUMENT_TYPES.keys()),
            },
        ),
    )
