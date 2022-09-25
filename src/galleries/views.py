import re
from urllib.parse import quote

import magic
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import reverse
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from .forms import GalleryCreateForm
from .models import Gallery
from .models import GalleryFile
from audios.models import Audio
from documents.models import Document
from pictures.models import Picture
from utils.mixins import OwnerOrAdminMixin
from utils.slugify import unique_slugify
from videos.models import Video


class GalleryManageListView(ListView):
    """List all galleries owned by this user."""

    model = Gallery
    template_name = "gallery_manage_list.html"

    def get_queryset(self, *args, **kwargs):
        """Return QS with all galleries owned by the logged-in user."""
        return Gallery.objects.filter(owner=self.request.user)


class GalleryManageCreateView(LoginRequiredMixin, CreateView):
    """The gallery create view."""

    model = Gallery
    template_name = "gallery_manage_create.html"
    form_class = GalleryCreateForm

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
                if mime in settings.ALLOWED_PICTURE_TYPES:
                    Picture.objects.create(
                        gallery=gallery,
                        original=f,
                        original_filename=f.name,
                        title=f.name,
                    )
                elif mime in settings.ALLOWED_VIDEO_TYPES:
                    Video.objects.create(
                        gallery=gallery,
                        original=f,
                        original_filename=f.name,
                        title=f.name,
                    )
                elif mime in settings.ALLOWED_AUDIO_TYPES:
                    Audio.objects.create(
                        gallery=gallery,
                        original=f,
                        original_filename=f.name,
                        title=f.name,
                    )
                elif mime in settings.ALLOWED_DOCUMENT_TYPES:
                    Document.objects.create(
                        gallery=gallery,
                        original=f,
                        original_filename=f.name,
                        title=f.name,
                    )
                else:
                    messages.warning(
                        request,
                        f"File type {mime} not supported for file: {f.name} - skipping file",
                    )
            if gallery.galleryfiles.exists():
                messages.success(
                    request,
                    f"Gallery created! Pictures: {gallery.pictures.count()}, Videos: {gallery.videos.count()}, Audios: {gallery.audios.count()}, Documents: {gallery.documents.count()}",
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


class GalleryManageDetailView(OwnerOrAdminMixin, DetailView):
    """Show a gallery to the owner or an admin."""

    model = Gallery
    template_name = "gallery_manage_detail.html"

    def get_context_data(self, *args, **kwargs):
        """Paginate."""
        context = super().get_context_data(*args, **kwargs)
        paginator = Paginator(
            self.object.galleryfiles.all(),
            settings.GALLERY_MANAGER_DEFAULT_PAGINATE_COUNT,
        )
        page_number = self.request.GET.get("page")
        context["page_obj"] = paginator.get_page(page_number)
        return context


class GalleryManageUpdateView(OwnerOrAdminMixin, UpdateView):
    """Allow the gallery owner or an admin to update a gallery."""

    model = Gallery
    template_name = "gallery_manage_update.html"
    fields = ["name", "description", "tags", "attribution"]


class GalleryManagePublishView(OwnerOrAdminMixin, UpdateView):
    """Allow the gallery owner or an admin to publish an unpublished gallery."""

    model = Gallery
    template_name = "gallery_manage_publish.html"
    fields = []

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        if self.get_object().status != "UNPUBLISHED":
            raise PermissionDenied("Gallery status must be unpublished!")

    def form_valid(self, form):
        self.object.status = "PUBLISHED"
        self.object.save()
        messages.success(
            self.request,
            f"Gallery '{self.object.name}' ({self.object.uuid}) has been published!",
        )
        return redirect(reverse("galleries:gallery_manage_list"))


class GalleryManageUnpublishView(OwnerOrAdminMixin, UpdateView):
    """Allow the gallery owner or an admin to unpublish a gallery."""

    model = Gallery
    template_name = "gallery_manage_unpublish.html"
    fields = []

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        if self.get_object().status != "PUBLISHED":
            raise PermissionDenied("Gallery must be published!")

    def form_valid(self, form):
        self.object.status = "UNPUBLISHED"
        self.object.save()
        messages.success(
            self.request,
            f"Gallery '{self.object.name}' ({self.object.uuid}) has been unpublished!",
        )
        return redirect(reverse("galleries:gallery_manage_list"))


class GalleryFileManageUpdateView(OwnerOrAdminMixin, UpdateView):
    """Allow the gallery owner or an admin to update a galleryfile."""

    model = GalleryFile
    fields = ["title", "description", "source", "tags"]

    def get_template_name(self):
        if self.request.is_htmx:
            return "includes/galleryfile_form.html"
        else:
            return "galleryfile_manage_update.html"


# PUBLIC VIEWS ##############################


class GalleryPublicListView(ListView):
    """List all published galleries."""

    model = Gallery
    template_name = "gallery_public_list.html"

    def get_queryset(self, *args, **kwargs):
        """
        Return QS with all published galleries."""
        return Gallery.objects.filter(status="PUBLISHED")


class GalleryPublicDetailView(DetailView):
    """Show a gallery."""

    model = Gallery
    template_name = "gallery_public_detail.html"

    def get_object(self, *args, **kwargs):
        """Only show this gallery if it is published."""
        return get_object_or_404(Gallery, slug=self.kwargs["slug"], status="PUBLISHED")

    def get_context_data(self, *args, **kwargs):
        """Only get published files and paginate."""
        context = super().get_context_data(*args, **kwargs)
        files = self.object.galleryfiles.filter(status="PUBLISHED")
        paginator = Paginator(files, 6)
        page_number = self.request.GET.get("page")
        context["page_obj"] = paginator.get_page(page_number)
        return context


def AccelMediaView(request, path):
    """This view uses Nginx X-Accel-Redirect to serve files.

    This means the request goes to Django and can be validated before telling Nginx what to return.

    In this view we just check if the Gallery is published and return a 404 if not.
    """
    print(path)
    # check file access by getting Gallery uuid from the path
    if match := re.match(
        r".*?/gallery_([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/(?:picture|video|audio|document)_([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).*?",
        path,
    ):
        # return 404 if the Gallery containing this file is not published,
        # unless the owner of the file or an admin is requesting it
        try:
            gallery = Gallery.objects.get(uuid=match.group(1))
        except Gallery.DoesNotExist:
            raise Http404("Gallery UUID not found")

        if gallery.status != "PUBLISHED":
            # gallery is not published but we might still want to show the file anyway
            if gallery.owner != request.user and not request.user.is_superuser:
                raise Http404("Gallery is not published")

        # return 404 if the file is unpublished
        try:
            galleryfile = GalleryFile.objects.get(uuid=match.group(2))
        except GalleryFile.DoesNotExist:
            raise Http404("File UUID not found")

        if galleryfile.status != "PUBLISHED":
            # file is not published but we might still want to show the file anyway
            if (
                galleryfile.gallery.owner != request.user
                and not request.user.is_superuser
            ):
                raise Http404("File is not published")

        response = HttpResponse(status=200)
        del response["Content-Type"]
        response["X-Accel-Redirect"] = f"/public/{quote(path)}"
        return response
    else:
        raise Http404("Unable to find Gallery or GalleryFile uuid")
