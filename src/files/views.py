import logging
import re
from pathlib import Path
from urllib.parse import quote
from users.models import User

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import assign_perm

from audios.models import Audio
from documents.models import Document
from files.forms import UploadForm
from files.mixins import FilesApprovalMixin
from files.models import BaseFile
from files.models import StatusChoices
from pictures.models import Picture
from videos.models import Video

logger = logging.getLogger("bma")


class FilesManageListView(LoginRequiredMixin, ListView):
    template_name = "files_manage_list.html"
    model = BaseFile

    def get_queryset(self):
        return BaseFile.objects.filter(
            owner=self.request.user,
        ).order_by("-created")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context = self._latest_files_context(context)
        return context

    def _latest_files_context(self, context: dict):
        context["latest_picture"] = self._query_latest_file(Picture)
        context["latest_video"] = self._query_latest_file(Video)
        context["latest_audio"] = self._query_latest_file(Audio)
        context["latest_document"] = self._query_latest_file(Document)
        return context

    def _query_latest_file(self, model):
        try:
            return model.objects.filter(owner=self.request.user).latest("created")
        except BaseFile.DoesNotExist:
            return ""


class FilesManageDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "files_manage_delete.html"
    model = BaseFile
    success_url = reverse_lazy("files:manage")

    def form_valid(self, form):
        messages.success(
            self.request,
            f"File {self.object.title} was deleted",
        )
        return super().form_valid(form)


class FilesManageDetailView(LoginRequiredMixin, DetailView):
    template_name = "files_manage_detail.html"
    model = BaseFile


class FilesManageEditView(LoginRequiredMixin, UpdateView):
    template_name = "files_manage_edit.html"
    model = BaseFile
    fields = ["title", "attribution", "source", "description"]
    success_url = reverse_lazy("files:manage")


class FilesUploadView(LoginRequiredMixin, FormView):
    template_name = "upload.html"
    form_class = UploadForm


class FilesApprovalUpdateView(PermissionRequiredMixin, FilesApprovalMixin, UpdateView):
    return_403 = True
    permission_required = "files.approve_basefile"
    allowed_approval_status = StatusChoices.PENDING_MODERATION
    template_approval_type = "approve"
    updated_status = StatusChoices.UNPUBLISHED
    error_msg_postfix = "not approved"
    success_msg_postfix = "approved"

    def form_valid(self, form):
        """Assign permissions for owner"""
        assign_perm("publish_basefile", self.object.owner, self.object)
        assign_perm("unpublish_basefile", self.object.owner, self.object)
        return super().form_valid(form)


class FilesPublishUpdateView(PermissionRequiredMixin, FilesApprovalMixin, UpdateView):
    return_403 = True
    permission_required = "files.publish_basefile"
    allowed_approval_status = StatusChoices.UNPUBLISHED
    template_approval_type = "publish"
    updated_status = StatusChoices.PUBLISHED
    error_msg_postfix = "not published"
    success_msg_postfix = "published"


class FilesUnpublishUpdateView(PermissionRequiredMixin, FilesApprovalMixin, UpdateView):
    return_403 = True
    permission_required = "files.unpublish_basefile"
    allowed_approval_status = StatusChoices.PUBLISHED
    template_approval_type = "unpublish"
    updated_status = StatusChoices.UNPUBLISHED
    error_msg_postfix = "not unpublished"
    success_msg_postfix = "unpublished"


def bma_media_view(request, path, accel):
    """Serve media files using nginx x-accel-redirect, or serve directly for dev use."""
    # get BaseFile uuid from the path
    if match := re.match(
        r".*?/bma_(?:picture|video|audio|document)_([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}).*?",
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

        if not request.user.has_perm("files.view_basefile", dbfile) and not User.get_anonymous().has_perm("files.view_basefile", dbfile):
            # neither the current user nor the anonymous user has permissions to view this file
            raise Http404()

        # check if the file exists in the filesystem
        if not Path(dbfile.original.path).exists():
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
            f = open(Path(settings.MEDIA_ROOT) / Path(path), "rb")
            response = FileResponse(f, status=200)
        # all good
        return response
    else:
        # regex parsing failed
        logger.debug("Unable to parse filename regex to find file UUID, returning 404")
        raise Http404()


class FileBrowserView(TemplateView):
    template_name = "filebrowser.html"
