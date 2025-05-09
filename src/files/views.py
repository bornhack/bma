"""File views."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from urllib.parse import quote

import shortuuid
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import Form
from django.http import FileResponse
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django_filters.views import FilterView
from django_tables2.paginators import LazyPaginator
from django_tables2.views import SingleTableMixin
from guardian.shortcuts import get_objects_for_user

from albums.filters import AlbumFilter
from albums.forms import AlbumAddFilesForm
from albums.forms import AlbumRemoveFilesForm
from albums.models import Album
from albums.tables import AlbumTable
from hitcounter.utils import count_hit
from images.models import ImageVersion
from jobs.filters import JobFilter
from jobs.models import BaseJob
from jobs.tables import JobTable
from permissions.tables import PermissionTable
from tags.filters import TagFilter
from tags.forms import TagForm
from tags.mixins import TagViewMixin
from tags.models import BmaTag
from tags.models import TaggedFile
from tags.tables import TaggingTable
from tags.tables import TagTable
from utils.auth import support_authbearer_user
from utils.mixins import CuratorGroupRequiredMixin

from .filters import FileFilter
from .forms import CropCenterForm
from .forms import FileMultipleActionForm
from .forms import UploadForm
from .mixins import FileChangeViewMixin
from .mixins import FileViewMixin
from .models import BaseFile
from .models import Thumbnail
from .models import ThumbnailSource
from .tables import FileTable

if TYPE_CHECKING:
    from guardian.models import GroupObjectPermission
    from guardian.models import UserObjectPermission

logger = logging.getLogger("bma")


class FileUploadView(LoginRequiredMixin, FormView):  # type: ignore[type-arg]
    """The upload view of many files. Uses the API and a js client to upload."""

    template_name = "upload.html"
    form_class = UploadForm


class FileListView(SingleTableMixin, FilterView):
    """File list view."""

    table_class = FileTable
    template_name = "file_list.html"
    filterset_class = FileFilter
    context_object_name = "files"
    paginator_class = LazyPaginator

    def get_template_names(self) -> list[str]:
        """Template name depends on the type of listview."""
        return [f"{self.request.resolver_match.url_name}.html"]

    def get_queryset(self, queryset: models.QuerySet[BaseFile] | None = None) -> models.QuerySet[BaseFile]:
        """Use bmanager to get juicy file objects."""
        return (  # type: ignore[no-any-return]
            BaseFile.bmanager.get_permitted(user=self.request.user)
            .prefetch_image_version_list()
            .prefetch_thumbnail_list()
            .prefetch_active_albums_list(recursive=True)
            .prefetch_tag_list()
            .annotate_job_counts()
        )

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, Form]:
        """Add form to the context."""
        context = super().get_context_data(**kwargs)
        context["file_action_form"] = FileMultipleActionForm()
        context["grid_url"] = reverse("files:file_list_grid")
        context["table_url"] = reverse("files:file_list_table")

        return context  # type: ignore[no-any-return]


class FileDetailView(DetailView):  # type: ignore[type-arg]
    """File detail view. Shows a single file."""

    model = BaseFile
    pk_url_kwarg = "file_uuid"
    context_object_name = "file"

    def get_template_names(self) -> list[str]:
        """Template name depends on the type of detailview."""
        return [f"{self.request.resolver_match.url_name}.html"]  # type: ignore[union-attr]

    def get_object(self, queryset: models.QuerySet[BaseFile] | None = None) -> BaseFile:
        """Check permissions before returning the file."""
        try:
            basefile = (
                BaseFile.bmanager.prefetch_image_version_list()
                .prefetch_thumbnail_list()
                .prefetch_active_albums_list()
                .get(pk=self.kwargs["file_uuid"])
            )
        except BaseFile.DoesNotExist as e:
            raise Http404 from e
        if not basefile.permitted(user=self.request.user):
            # the current user does not have permissions to view this file
            raise PermissionDenied

        # count the hit
        count_hit(self.request, basefile)

        # all good
        return basefile  # type: ignore[no-any-return]

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, Form]:
        """Add sizes and ratios context."""
        context = super().get_context_data(**kwargs)
        context["sizes"] = self.get_object().thumbnails.all().values_list("width", flat=True).distinct()
        context["ratios"] = set(self.get_object().thumbnails.all().values_list("aspect_ratio", flat=True))
        context["prefix"] = f"{self.request.scheme}://{self.request.get_host()}"
        return context


@support_authbearer_user
def bma_media_view(request: HttpRequest, *, path: str, accel: bool) -> FileResponse | HttpResponse:
    """Authenticated file serving view for shortuuid based BMA URLs.

    This view serves media files using nginx x-accel-redirect, or directly for dev use,
    controlled by the accel argument.

    This view is used in browsers as well as by api clients, so it permits both regular
    sessioncookie based auth and api token auth.

    BMA file serving is done using a prefix based on the class of file. The path under
    settings.MEDIA_URL is:
      - /oi/shortuuid.ext for original Image files
      - /ov/shortuuid.ext for original Video files
      - /oa/shortuuid.ext for original Audio files
      - /od/shortuuid.ext for original Document files
      - /ts/shortuuid.ext for ThumbnailSource files
      - /iv/shortuuid.ext for ImageVersion files (smaller versions of original images)
      - /t/shortuuid.ext for Thumbnail files

    Args:
      request(HttpRequest): The HTTP request object
      path(str): The requested path under settings.MEDIA_URL
      accel(bool): Set True to serve using nginx, False to serve files with Djangos devserver.

    Returns: An HttpResponse or FileResponse.
    """
    try:
        prefix, filename = path.split("/")
        shortid, _ = filename.split(".")
    except ValueError as e:
        raise Http404 from e

    pk = shortuuid.decode(shortid)

    try:
        obj = None
        if prefix[0] == "o":
            # original
            obj = BaseFile.objects.get(pk=pk)
            basefile = obj
            filepath = obj.original.path

        elif prefix == "ts":
            # thumbnailsource
            obj = ThumbnailSource.objects.get(pk=pk)
            basefile = obj.basefile
            filepath = obj.source.path

        elif prefix == "iv":
            # imageversion
            obj = ImageVersion.objects.get(pk=pk)
            basefile = obj.image
            filepath = obj.imagefile.path

        elif prefix == "t":
            # thumbnail
            obj = Thumbnail.objects.get(pk=pk)
            basefile = obj.basefile
            filepath = obj.imagefile.path

    except ObjectDoesNotExist as e:
        raise Http404 from e

    # check if the obj was found and file exists in the filesystem
    if not obj or not Path(filepath).exists():
        raise Http404

    # check if the basefile this obj is related to is permitted for the user
    if not basefile.permitted(user=request.user):
        raise PermissionDenied

    # count the hit
    count_hit(request, basefile)

    # OK, show the file
    response: FileResponse | HttpResponse
    if accel:
        # we are using nginx x-accel-redirect
        response = HttpResponse(status=200)
        # remove the Content-Type header to allow nginx to add it
        del response["Content-Type"]
        public_url = str(Path(filepath).relative_to(settings.MEDIA_ROOT)).encode()
        response["X-Accel-Redirect"] = f"/public/{quote(public_url)}"
    else:
        # we are serving the file locally
        f = Path.open(Path(settings.MEDIA_ROOT) / filepath, "rb")
        response = FileResponse(f, filename=Path(filepath).name, status=200)
        response["Content-Type"] = obj.mimetype
        # cache for an hour in development for a more
        # pleasant (and closer to realworld) dev experience
        response["Cache-Control"] = "max-age=3600"
    # all good
    return response


class FileBrowserView(TemplateView):
    """The file browser view."""

    template_name = "filebrowser.html"


class FileMultipleActionView(LoginRequiredMixin, FormView):  # type: ignore[type-arg]
    """The view of many files and many actions."""

    form_class = FileMultipleActionForm

    def get_form(self, form_class: FileMultipleActionForm | None = None) -> FileMultipleActionForm:  # type: ignore[override]
        """Return an instance of the form vith appropriate choices."""
        form = super().get_form()
        # any filters in the view decide what choices are actually rendered in the html form,
        # but all permitted files uuids are added as choices to make sure validation passes
        form.fields["selection"].choices = BaseFile.bmanager.get_permitted(user=self.request.user).values_list(
            "pk", "pk"
        )
        return form  # type: ignore[no-any-return]

    def form_valid(self, form: Form) -> HttpResponse:
        """Determine action and act accordingly."""
        if form.cleaned_data["action"] == "create_album":
            now = timezone.now().isoformat()
            album = Album(
                title=f"Album-Created-{now}",
                description=f"Album created {now}",
                owner=self.request.user,  # type: ignore[misc]
            )
            album.save()
            album.files.set(form.cleaned_data["selection"])
            album.add_initial_permissions()
            return redirect(album)

        elif form.cleaned_data["action"] == "add_to_album":  # noqa: RET505
            # render a form to pick the album to which the files should be added
            albums = get_objects_for_user(self.request.user, "change_album", klass=Album.bmanager.all())
            # only show albums which doesn't already have all the files as members
            form_uuids = form.cleaned_data["selection"]
            form_albums = []
            for album in albums:
                album_uuids = [str(f.pk) for f in album.active_files_list]
                if len(set(album_uuids).intersection(set(form_uuids))) == len(form_uuids):
                    # all selected files are already a member of this album, skip it
                    continue
                form_albums.append(album)
            album_add_form = AlbumAddFilesForm(initial={"files_to_add": form.cleaned_data["selection"]})
            choices = [(album.pk, f"{album.title} ({len(album.active_files_list)})") for album in form_albums]
            album_add_form.fields["album"].choices = choices  # type: ignore[attr-defined]
            if len(choices) == 1:
                album_add_form.initial["album"] = choices[0]  # type: ignore[index]
            album_add_form.fields["files_to_add"].choices = [(x, x) for x in form.cleaned_data["selection"]]  # type: ignore[attr-defined]
            return render(self.request, "files_add_to_album.html", context={"form": album_add_form})

        elif form.cleaned_data["action"] == "remove_from_album":
            # render a form to pick the album from which the files should be removed
            albums = get_objects_for_user(self.request.user, "change_album", klass=Album.bmanager.all())
            for basefile in form.cleaned_data["selection"]:
                albums = albums.filter(files__in=[basefile])
            # put the form together
            album_remove_form = AlbumRemoveFilesForm(
                initial={
                    "files_to_remove": form.cleaned_data["selection"],
                    "album": albums.first().pk,  # default to selecting the first album
                }
            )
            album_remove_form.fields["album"].choices = albums.values_list("pk", "title")  # type: ignore[attr-defined]
            album_remove_form.fields["files_to_remove"].choices = [(x, x) for x in form.cleaned_data["selection"]]  # type: ignore[attr-defined]
            return render(self.request, "files_remove_from_album.html", context={"form": album_remove_form})
        # please mypy
        return None  # type: ignore[return-value]

    def form_invalid(self, form: Form) -> HttpResponse:
        """Show an error message and return to fromurl or file list page."""
        logger.error(form)
        messages.error(self.request, "There was a validation issue with the form:")
        messages.error(self.request, str(form.errors))
        if "fromurl" in form.data:
            return redirect(form.data["fromurl"])
        return redirect(reverse("files:file_list"))


########## File job and album views ######################################################


class FileJobsView(FileViewMixin, SingleTableMixin, FilterView):
    """File jobs view. Shows all jobs for a file."""

    template_name = "file_jobs.html"
    pk_url_kwarg = "file_uuid"
    context_object_name = "file"
    table_class = JobTable
    filterset_class = JobFilter

    def get_queryset(self, queryset: models.QuerySet[BaseJob] | None = None) -> models.QuerySet[BaseJob]:
        """Get jobs."""
        return BaseJob.bmanager.filter(basefile=self.file)  # type: ignore[no-any-return]

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, str]:
        """Add total_jobs to context."""
        context = super().get_context_data(**kwargs)
        context["total_jobs"] = self.file.jobs.count()
        return context


class FileAlbumsView(FileViewMixin, SingleTableMixin, FilterView):
    """File albums view. Shows all albums a file is currently member of."""

    template_name = "file_albums.html"
    pk_url_kwarg = "file_uuid"
    context_object_name = "file"
    table_class = AlbumTable
    filterset_class = AlbumFilter

    def get_table_data(self) -> models.QuerySet[Album]:
        """Get albums."""
        return Album.bmanager.filter(uuid__in=self.object.albums.all().values_list("uuid", flat=True))

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, str]:
        """Add total_albums to context."""
        context = super().get_context_data(**kwargs)
        context["total_albums"] = self.file.albums.count()
        return context


########## File tag views ######################################################


class FileTagListView(FileViewMixin, SingleTableMixin, FilterView):
    """File tag list view."""

    table_class = TagTable
    template_name = "file_tags.html"
    filterset_class = TagFilter
    context_object_name = "tags"

    def get_table_kwargs(self) -> dict[str, BaseFile | tuple[str, str, str]]:
        """Exclude columns which don't make sense in context of a single file."""
        return {"basefile": self.file, "exclude": ("tagged_files", "taggings", "taggings_per_file")}

    def get_queryset(self, queryset: models.QuerySet[BmaTag] | None = None) -> models.QuerySet[BmaTag]:
        """Get tags for this file."""
        return BmaTag.objects.filter(taggings__content_object=self.file).annotate(weight=models.Count("name"))  # type: ignore[no-any-return]


class FileTagCreateView(CuratorGroupRequiredMixin, FileViewMixin, FormView):  # type: ignore[type-arg]
    """View to add one or more tags to a file."""

    form_class = TagForm
    template_name = "file_tag_create.html"

    def form_valid(self, form: TagForm) -> HttpResponse:
        """Apply the tag(s)."""
        self.file.parse_and_add_tags(tags=form.cleaned_data["tags"], tagger=self.request.user)
        messages.success(self.request, "Tag(s) added.")
        return redirect(self.file)


class FileTagDetailView(TagViewMixin, SingleTableMixin, ListView):  # type: ignore[type-arg,misc]
    """File tag detail view. Shows a list of taggings of a tag on a file."""

    table_class = TaggingTable
    template_name = "file_tag_tagging_list.html"
    model = TaggedFile

    def get_queryset(self, queryset: models.QuerySet[TaggedFile] | None = None) -> models.QuerySet[TaggedFile]:
        """Get tags for this file."""
        # count the hit
        count_hit(self.request, self.tag)
        return self.file.taggings.filter(tag=self.tag)  # type: ignore[no-any-return]


class FileTagDeleteView(TagViewMixin, DeleteView):  # type: ignore[type-arg,misc]
    """File untagging view. Removes a users tagging of a tag from a file."""

    model = TaggedFile

    def get_object(self, queryset: models.QuerySet[TaggedFile] | None = None) -> TaggedFile:
        """Get the TaggedFile object if it exists."""
        return get_object_or_404(self.file.taggings.all(), tag=self.tag, tagger=self.request.user)  # type: ignore[no-any-return]

    def form_valid(self, form: Form) -> HttpResponse:
        """Untag and redirect to file details."""
        self.object.delete()
        messages.success(self.request, "Tag deleted.")
        return redirect(self.file)


########## File permission views ######################################################


class FilePermissionsView(FileViewMixin, SingleTableMixin, TemplateView):
    """File Permissions view. Shows all Permissions (user and group) for a file."""

    template_name = "file_permissions.html"
    pk_url_kwarg = "file_uuid"
    context_object_name = "file"
    table_class = PermissionTable

    def get_table_data(self) -> "list[UserObjectPermission| GroupObjectPermission]":
        """Get the data for the table."""
        return list(self.file.user_permissions.all()) + list(self.file.group_permissions.all())


######### File Center Crop views ######################################################


class FileCropCenterView(FileChangeViewMixin, FormView[CropCenterForm]):
    """View to pick the center of a ThumbnailSource or Image."""

    form_class = CropCenterForm
    template_name = "file_crop_center.html"

    def get_initial(self) -> dict[str, Any]:
        """Lookup the data for the form."""
        initial = super().get_initial()

        if hasattr(self.file, "thumbnailsource"):
            initial["center_x"] = self.file.thumbnailsource.crop_center_x
            initial["center_y"] = self.file.thumbnailsource.crop_center_y
        elif self.file.filetype == "image":
            initial["center_x"] = self.file.crop_center_x
            initial["center_y"] = self.file.crop_center_y
        else:
            error = "ThumbnailSource does not exist"
            raise Http404(error)

        return initial

    def form_valid(self, form: CropCenterForm) -> HttpResponseRedirect:
        """Apply the crop center."""
        if hasattr(self.file, "thumbnailsource"):
            self.file.thumbnailsource.crop_center_x = form.cleaned_data["center_x"]
            self.file.thumbnailsource.crop_center_y = form.cleaned_data["center_y"]
            self.file.thumbnailsource.save()
            self.file.create_thumbnail_jobs()
            messages.success(self.request, "Thumbnail Source crop center saved.")
        elif self.file.filetype == "image":
            self.file.crop_center_x = form.cleaned_data["center_x"]
            self.file.crop_center_y = form.cleaned_data["center_y"]
            self.file.save()
            self.file.create_thumbnail_jobs()
            messages.success(self.request, "Image crop center saved.")
        else:
            messages.info(self.request, "No changes made")

        return redirect(self.file)
