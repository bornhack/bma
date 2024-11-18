"""File views."""

import logging
import mimetypes
import re
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import Form
from django.http import FileResponse
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
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
from django_tables2.views import SingleTableMixin
from guardian.shortcuts import get_objects_for_user

from albums.forms import AlbumAddFilesForm
from albums.forms import AlbumRemoveFilesForm
from albums.models import Album
from hitcounter.utils import count_hit
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
from .forms import FileMultipleActionForm
from .forms import UploadForm
from .mixins import FileViewMixin
from .models import BaseFile
from .tables import FileTable

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

    def get_queryset(self, queryset: models.QuerySet[BaseFile] | None = None) -> models.QuerySet[BaseFile]:
        """Use bmanager to get juicy file objects."""
        return BaseFile.bmanager.all()  # type: ignore[no-any-return]

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, Form]:
        """Add form to the context."""
        context = super().get_context_data(**kwargs)
        context["file_action_form"] = FileMultipleActionForm()
        return context  # type: ignore[no-any-return]


class FileDetailView(DetailView):  # type: ignore[type-arg]
    """File detail view. Shows a single file."""

    template_name = "file_detail.html"
    model = BaseFile
    pk_url_kwarg = "file_uuid"
    context_object_name = "file"

    def get_object(self, queryset: models.QuerySet[BaseFile] | None = None) -> BaseFile:
        """Check permissions before returning the file."""
        basefile = get_object_or_404(BaseFile.bmanager.filter(pk=self.kwargs["file_uuid"]))
        if not basefile.permitted(user=self.request.user):
            # the current user does not have permissions to view this file
            raise PermissionDenied

        # count the hit
        count_hit(self.request, basefile)

        # all good
        return basefile  # type: ignore[no-any-return]


@support_authbearer_user
def bma_media_view(request: HttpRequest, *, path: str, accel: bool) -> FileResponse | HttpResponse:
    """Serve media files using nginx x-accel-redirect, or serve directly for dev use.

    This view is used in browsers as well as by api clients, so it permits both regular
    sessioncookie based auth and api token auth.
    """
    # get last uuid from the path
    match = re.match(
        r"^.*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).*$",
        path,
    )
    if not match:
        # regex parsing failed
        logger.debug("Unable to parse filename regex to find file UUID, returning 404")
        raise Http404

    # get the file from database
    try:
        dbfile = BaseFile.objects.get(uuid=match.group(1))
    except BaseFile.DoesNotExist as e:
        logger.debug(
            f"File UUID {match.group(1)} not found in database, returning 404",
        )
        raise Http404 from e

    # check file permissions
    if not dbfile.permitted(user=request.user):
        # the current user does not have permissions to view this file
        raise PermissionDenied

    # check if the file exists in the filesystem
    if not Path(dbfile.original.path).exists():
        logger.debug(f"File does not exist on dist: {dbfile.original.path}")
        raise Http404

    # count the hit
    count_hit(request, dbfile)

    # OK, show the file
    response: FileResponse | HttpResponse
    if accel:
        # we are using nginx x-accel-redirect
        response = HttpResponse(status=200)
        # remove the Content-Type header to allow nginx to add it
        del response["Content-Type"]
        response["X-Accel-Redirect"] = f"/public/{quote(path)}"
    else:
        # we are serving the file locally
        f = Path.open(Path(settings.MEDIA_ROOT) / path, "rb")
        response = FileResponse(f, filename=Path(path).name, status=200)
        mimetype, _encoding = mimetypes.guess_type(path, strict=False)
        if mimetype:
            response["Content-Type"] = mimetype
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
        form.fields["selection"].choices = BaseFile.bmanager.all().values_list("pk", "pk")
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


########## File tag views ######################################################


class FileTagListView(FileViewMixin, SingleTableMixin, FilterView):
    """File tag list view."""

    table_class = TagTable
    template_name = "file_tags.html"
    filterset_class = TagFilter
    context_object_name = "tags"

    def get_queryset(self, queryset: models.QuerySet[BmaTag] | None = None) -> models.QuerySet[BmaTag]:
        """Get tags for this file."""
        return self.file.tags.annotate(taggedfile_uuid=models.Value(self.file.uuid)).all()  # type: ignore[no-any-return]


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
