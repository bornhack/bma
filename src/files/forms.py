from django import forms

from .models import BaseFile


class UploadForm(forms.ModelForm):
    files = forms.FileField(widget=forms.ClearableFileInput())

    class Meta:
        model = BaseFile
        fields = ["license", "attribution"]
