import re
from urllib.parse import quote

import magic
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView

from .forms import GalleryForm
from .models import Gallery
from .models import GalleryFile
from audios.models import Audio
from documents.models import Document
from photos.models import Photo
from utils.slugify import unique_slugify
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
            gallery.slug = unique_slugify(
                gallery.name,
                slugs_in_use=Gallery.objects.all().values_list("slug", flat=True),
            )
            gallery.save()
            # save tags
            form.save_m2m()
            # save files
            for f in files:
                mime = magic.from_buffer(f.read(), mime=True)
                if mime in settings.ALLOWED_PHOTO_TYPES:
                    Photo.objects.create(
                        gallery=gallery,
                        original=f,
                        original_filename=f.name,
                    )
                elif mime in settings.ALLOWED_VIDEO_TYPES:
                    Video.objects.create(
                        gallery=gallery,
                        original=f,
                        original_filename=f.name,
                    )
                elif mime in settings.ALLOWED_AUDIO_TYPES:
                    Audio.objects.create(
                        gallery=gallery,
                        original=f,
                        original_filename=f.name,
                    )
                elif mime in settings.ALLOWED_DOCUMENT_TYPES:
                    Document.objects.create(
                        gallery=gallery,
                        original=f,
                        original_filename=f.name,
                    )
                else:
                    messages.warning(
                        request,
                        f"File type {mime} not supported for file: {f.name} - skipping file",
                    )
            if (
                gallery.photos.exists()
                or gallery.videos.exists()
                or gallery.audios.exists()
                or gallery.documents.exists()
            ):
                messages.success(
                    request,
                    f"Gallery created! Photos: {gallery.photos.count()}, Videos: {gallery.videos.count()}, Audios: {gallery.audios.count()}, Documents: {gallery.documents.count()}",
                )
                return redirect(gallery.get_absolute_url())
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
        return Gallery.objects.filter(status="PUBLISHED") | Gallery.objects.filter(
            owner=self.request.user,
        )


class GalleryDetailView(DetailView):
    """Show a gallery."""

    model = Gallery
    template_name = "gallery_detail.html"

    def get_object(self, *args, **kwargs):
        gallery = get_object_or_404(Gallery, slug=self.kwargs["slug"])
        if (
            gallery.owner == self.request.user
            or gallery.status == "PUBLISHED"
            or self.request.user.is_superuser
        ):
            return gallery
        raise Http404("Gallery not found")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.object.owner == self.request.user or self.request.user.is_superuser:
            # get all files
            files = (
                GalleryFile.objects.filter(photo__gallery=self.object)
                | GalleryFile.objects.filter(video__gallery=self.object)
                | GalleryFile.objects.filter(audio__gallery=self.object)
                | GalleryFile.objects.filter(document__gallery=self.object)
            )
        else:
            # only get published files
            files = GalleryFile.objects.filter(gallery=self.object, status="PUBLISHED")
        paginator = Paginator(files, 3)
        page_number = self.request.GET.get("page")
        context["page_obj"] = paginator.get_page(page_number)
        return context


def AccelMediaView(request, path):
    """This view uses Nginx X-Accel-Redirect to serve files.

    This means the request goes to Django and can be validated before telling
    Nginx what to return.

    In this view we just check if the Gallery is published and return a 404 if not.
    """

    # check file access by getting Gallery uuid from the path
    if match := re.match(
        ".*?/gallery_([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/.*?",
        path,
    ):
        # return 404 if the Gallery containing this file is unpublished
        get_object_or_404(Gallery, uuid=match.group(1), status="PUBLISHED")
        # return 404 if the file is unpublished

        response = HttpResponse(status=200)
        del response["Content-Type"]
        response["X-Accel-Redirect"] = f"/public/{quote(path)}"
        return response
    else:
        raise Http404("Unable to find Gallery uuid")
