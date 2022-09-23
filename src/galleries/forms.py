from django import forms
from django.conf import settings

from .models import Gallery


class GalleryCreateForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ["name", "description", "tags", "license", "attribution"]
        # widgets = {"tags": taggit.forms.TagWidget(attrs={"data-role": "tagsinput"})}

    files = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "multiple": True,
                "accept": ",".join(settings.ALLOWED_PICTURE_TYPES.keys())
                + ",".join(settings.ALLOWED_VIDEO_TYPES.keys())
                + ",".join(settings.ALLOWED_AUDIO_TYPES.keys())
                + ",".join(settings.ALLOWED_DOCUMENT_TYPES.keys()),
            },
        ),
    )
