import magic
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.views.generic import ListView

from .forms import GalleryForm
from .models import Gallery
from photos.models import Photo


class GalleryCreateView(LoginRequiredMixin, CreateView):
    """The gallery create view. For now."""

    model = Gallery
    template_name = "gallery_create.html"
    form_class = GalleryForm
    success_url = "/"

    def get_initial(self):
        initial = super().get_initial()
        # initial = initial.copy()
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
                if mime.startswith("image/"):
                    Photo.objects.create(
                        gallery=gallery,
                        photo=f,
                        original_filename=f.name,
                    )
                else:
                    messages.warning(
                        request,
                        "File type {mime} not supported for file: {f.name}",
                    )
            messages.success(
                request,
                f"Gallery created! Photos: {gallery.gallery_photos.count()}",
            )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class GalleryListView(ListView):
    """List all galleries."""

    model = Gallery
    template_name = "gallery_list.html"

    def get_queryset(self, *args, **kwargs):
        return Gallery.objects.filter(published=True)
