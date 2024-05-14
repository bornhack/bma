"""File views."""
import logging
import re
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.forms import Form
from django.http import FileResponse
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import TemplateView
from django.views.generic import UpdateView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from guardian.shortcuts import get_objects_for_user

from .filters import FileFilter
from .forms import UpdateForm
from .forms import UploadForm
from .models import BaseFile
from .tables import FileTable

logger = logging.getLogger("bma")


class FileUploadView(LoginRequiredMixin, FormView):  # type: ignore[type-arg]
    """The upload view of many files."""

    template_name = "upload.html"
    form_class = UploadForm


class FileListView(SingleTableMixin, FilterView):
    """File list view."""

    table_class = FileTable
    template_name = "list.html"
    filterset_class = FileFilter
    context_object_name = "files"

    def get_queryset(self) -> QuerySet[BaseFile]:
        """Get files that are PUBLISHED or where the current user has view_basefile perms."""
        files = BaseFile.objects.filter(status="PUBLISHED") | get_objects_for_user(
            self.request.user,
            "files.view_basefile",
        )
        return files.distinct()  # type: ignore[no-any-return]


class FileDetailView(DetailView):  # type: ignore[type-arg]
    """File detail view. Shows a single file."""

    template_name = "detail.html"
    model = BaseFile

    def get_object(self, queryset: QuerySet[BaseFile] | None = None) -> BaseFile:
        """Check permissions before returning the file."""
        basefile = super().get_object(queryset=queryset)
        if not self.request.user.has_perm("files.view_basefile", basefile) and basefile.status != "PUBLISHED":
            # file is not PUBLISHED, and the current user does not have permissions to view this file
            raise PermissionDenied
        return basefile  # type: ignore[no-any-return]


class FileDeleteView(DeleteView):  # type: ignore[type-arg]
    """File delete view. Delete a single file."""

    template_name = "delete.html"
    model = BaseFile

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Check permissions before soft deleting file."""
        if not self.request.user.has_perm("files.delete_basefile", self.object):
            raise PermissionDenied
        self.object.update_status(new_status="PENDING_DELETION")
        return HttpResponseRedirect(reverse_lazy("files:detail", kwargs={"pk": self.object.uuid}))


class FileUpdateView(UpdateView):  # type: ignore[type-arg]
    """File update view. Update a single files attributes."""

    template_name = "update.html"
    model = BaseFile
    form_class = UpdateForm

    def get_object(self, queryset: QuerySet[BaseFile] | None = None) -> BaseFile:
        """Check permissions before returning the file."""
        basefile = super().get_object(queryset=queryset)
        if not self.request.user.has_perm("files.change_basefile", basefile):
            raise PermissionDenied
        return basefile  # type: ignore[no-any-return]


def bma_media_view(request: HttpRequest, path: str, *, accel: bool) -> FileResponse | HttpResponse:
    """Serve media files using nginx x-accel-redirect, or serve directly for dev use."""
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
    if not request.user.has_perm("files.view_basefile", dbfile) and dbfile.status != "PUBLISHED":
        # file is not PUBLISHED and the current user does not have permissions to view this file
        raise PermissionDenied

    # check if the file exists in the filesystem
    if not Path(dbfile.original.path).exists():
        raise Http404

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
        f = Path.open(Path(settings.MEDIA_ROOT) / Path(path), "rb")
        response = FileResponse(f, status=200)
    # all good
    return response


class FileBrowserView(TemplateView):
    """The file browser view."""

    template_name = "filebrowser.html"
