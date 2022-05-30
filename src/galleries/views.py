import magic
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.views.generic import ListView

from .forms import GalleryForm
from .models import Gallery
from audios.models import Audio
from documents.models import Document
from photos.models import Photo
from videos.models import Video


class GalleryCreateView(LoginRequiredMixin, CreateView):
    """The gallery create view. For now."""

    model = Gallery
    template_name = "gallery_create.html"
    form_class = GalleryForm
    success_url = "/"

    def get_initial(self):
        """Set initial values for the upload form."""
        initial = super().get_initial()
        initial["attribution"] = self.request.user.public_credit_name
        return initial

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist("files")
        if form.is_valid():
            gallery = form.save(commit=False)
            gallery.owner = request.user
            gallery.save()
            for f in files:
                mime = magic.from_buffer(f.read(), mime=True)
                if mime in settings.ALLOWED_PHOTO_TYPES:
                    Photo.objects.create(
                        gallery=gallery,
                        photo=f,
                        original_filename=f.name,
                    )
                elif mime in settings.ALLOWED_VIDEO_TYPES:
                    Video.objects.create(
                        gallery=gallery,
                        video=f,
                        original_filename=f.name,
                    )
                elif mime in settings.ALLOWED_AUDIO_TYPES:
                    Audio.objects.create(
                        gallery=gallery,
                        audio=f,
                        original_filename=f.name,
                    )
                elif mime in settings.ALLOWED_DOCUMENT_TYPES:
                    Document.objects.create(
                        gallery=gallery,
                        document=f,
                        original_filename=f.name,
                    )
                else:
                    messages.warning(
                        request,
                        f"File type {mime} not supported for file: {f.name} - skipping file",
                    )
            if (
                gallery.gallery_photos.exists()
                or gallery.gallery_videos.exists()
                or gallery.gallery_audios.exists()
                or gallery.gallery_documents.exists()
            ):
                messages.success(
                    request,
                    f"Gallery created! Photos: {gallery.gallery_photos.count()}, Videos: {gallery.gallery_videos.count()}, Audios: {gallery.gallery_audios.count()}, Documents: {gallery.gallery_documents.count()}",
                )
                return self.form_valid(form)
            else:
                messages.error(
                    request,
                    "Error: No valid files in gallery, gallery not created!",
                )
        # form_invalid() needs self.object defined
        self.object = None
        return self.form_invalid(form)


class GalleryListView(ListView):
    """List all galleries."""

    model = Gallery
    template_name = "gallery_list.html"

    def get_queryset(self, *args, **kwargs):
        return Gallery.objects.filter(published=True)
