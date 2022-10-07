from django import forms

from .models import BaseFile


class UploadForm(forms.ModelForm):
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))

    class Meta:
        model = BaseFile
        fields = ["license", "attribution"]
