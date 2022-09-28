import logging
import re
from pathlib import Path
from urllib.parse import quote

from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponse
from django.views.generic import FormView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from audios.models import Audio
from documents.models import Document

from files.forms import UploadForm
from files.models import BaseFile
from pictures.models import Picture
from videos.models import Video

logger = logging.getLogger("bma")


class FilesManageListView(LoginRequiredMixin, ListView):
    template_name = "files_manage_list.html"
    model = BaseFile

    def get_queryset(self):
        return BaseFile.objects.filter(owner=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        return self._latest_files_context(context)

    def _latest_files_context(self, context: dict):
        context["latest_picture"] = self._query_latest_file(Picture)
        context["latest_video"] = self._query_latest_file(Video)
        context["latest_audio"] = self._query_latest_file(Audio)
        context["latest_document"] = self._query_latest_file(Document)
        return context

    def _query_latest_file(self, model):
        try:
            return model.objects.filter(owner=self.request.user).latest('uuid')
        except BaseFile.DoesNotExist:
            return ""


class UploadView(LoginRequiredMixin, FormView):
    template_name = "upload.html"
    form_class = UploadForm


def BMAMediaView(request, path, accel):
    """Serve media files using nginx x-accel-redirect, or serve directly for dev use."""
    # get BaseFile uuid from the path
    if match := re.match(
        r".*?/(?:picture|video|audio|document)_([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).*?",
        path,
    ):
        # get the file from database
        try:
            dbfile = BaseFile.objects.get(uuid=match.group(1))
        except BaseFile.DoesNotExist:
            logger.debug(
                f"File UUID {match.group(1)} not found in database, returning 404",
            )
            raise Http404()

        if dbfile.status != "PUBLISHED":
            # file is not published but we might still want to show it
            if dbfile.owner != request.user and not request.user.is_superuser:
                logger.debug(
                    f"File UUID {match.group(1)} is not published and user is not owner or admin, returning 404",
                )
                raise Http404()

        # check if the file exists in the filesystem
        if not Path(dbfile.original.path).exists():
            logger.debug(
                f"File UUID {match.group(1)} does not exist on disk, returning 404",
            )
            raise Http404()

        # OK, show the file
        if accel:
            # we are using nginx x-accel-redirect
            response = HttpResponse(status=200)
            # remove the Content-Type header to allow nginx to add it
            del response["Content-Type"]
            response["X-Accel-Redirect"] = f"/public/{quote(path)}"
        else:
            # we are serving the file locally
            with open(dbfile.original.path, "rb") as f:
                response = FileResponse(f, status=200)
        # all good
        return response
    else:
        # regex parsing failed
        logger.debug("Unable to parse filename regex to find file UUID, returning 404")
        raise Http404()
