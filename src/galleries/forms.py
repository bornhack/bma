from django import forms

from .models import Gallery


class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ["name", "tags", "license", "attribution"]

    files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))
