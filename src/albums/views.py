"""Album views."""

import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import Form
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic import FormView
from django.views.generic import UpdateView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from guardian.shortcuts import get_objects_for_user

from files.filters import FileFilter
from files.forms import FileMultipleActionForm
from files.models import BaseFile
from files.tables import FileTable
from hitcounter.utils import count_hit
from utils.mixins import CuratorGroupRequiredMixin

from .filters import AlbumFilter
from .forms import AlbumAddFilesForm
from .forms import AlbumRemoveFilesForm
from .models import Album
from .tables import AlbumTable

logger = logging.getLogger("bma")


class AlbumListView(SingleTableMixin, FilterView):
    """Album list view."""

    model = Album
    table_class = AlbumTable
    template_name = "album_list.html"
    filterset_class = AlbumFilter
    context_object_name = "albums"

    def get_queryset(self) -> models.QuerySet[Album]:
        """Use bmanager to get rich album objects."""
        return Album.bmanager.all()


class AlbumDetailView(SingleTableMixin, FilterView):
    """Album detail view with file table and filter."""

    pk_url_kwarg = "album_uuid"
    template_name = "album_detail.html"
    table_class = FileTable
    filterset_class = FileFilter

    def get_template_names(self) -> list[str]:
        """Template name depends on the type of detailview."""
        return [f"{self.request.resolver_match.url_name}.html"]

    def get_object(self, queryset: models.QuerySet[Album] | None = None) -> Album:
        """Use the manager so the album object has prefetched active_files."""
        album = Album.bmanager.get(pk=self.kwargs["album_uuid"])
        # count the hit
        count_hit(self.request, album)
        return album  # type: ignore[no-any-return]

    def get_queryset(self) -> str:
        """Prefer a real bmanager qs over the list of files so each file obj has all needed info."""
        uuids = [f.pk for f in self.get_object().active_files_list]
        return BaseFile.bmanager.get_permitted(user=self.request.user).filter(pk__in=uuids)  # type: ignore[no-any-return]

    def get_context_data(self, **kwargs: dict[str, str]) -> dict[str, str]:
        """Add album to context."""
        context = super().get_context_data(**kwargs)
        context["album"] = self.get_object()
        context["file_action_form"] = FileMultipleActionForm()
        return context  # type: ignore[no-any-return]


class AlbumCreateView(CuratorGroupRequiredMixin, CreateView):  # type: ignore[type-arg]
    """Album create view."""

    template_name = "album_form.html"
    model = Album
    fields = ("title", "description")

    def get_form(self, form_class: Any | None = None) -> Form:  # noqa: ANN401
        """Return an instance of the form to be used in this view, only show permitted files in the form."""
        form = super().get_form()
        form.fields["files"].queryset = BaseFile.bmanager.get_permitted(user=self.request.user)
        return form  # type: ignore[no-any-return]

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Set album owner before saving."""
        album = form.save(commit=False)  # type: ignore[attr-defined]
        album.owner = self.request.user
        album.save()
        form.save_m2m()  # type: ignore[attr-defined]
        messages.success(self.request, f"Album {album.pk} created!")
        return HttpResponseRedirect(album.get_absolute_url())


class AlbumUpdateView(CuratorGroupRequiredMixin, UpdateView):  # type: ignore[type-arg]
    """Album update view."""

    template_name = "album_form.html"
    model = Album
    fields = ("title", "description")
    pk_url_kwarg = "album_uuid"

    def get_success_url(self) -> str:
        """Return to the album."""
        messages.success(self.request, "Album updated!")
        return reverse(self.get_object())


class AlbumAddFilesView(LoginRequiredMixin, FormView):  # type: ignore[type-arg]
    """Add files to an album.

    This view is used by FileMultipleActionView (in which case the form is rendered by
    that view, so files are preselected and only the album needs to be picked) and by
    AlbumDetailView (where album is preselected from the URL and the files need to be picked).
    """

    form_class = AlbumAddFilesForm
    template_name = "files_add_to_album.html"

    def get_form(self, form_class: AlbumAddFilesForm | None = None) -> AlbumAddFilesForm:  # type: ignore[override]
        """Return an instance of the form vith appropriate choices."""
        form = super().get_form()

        # do we have an album_uuid or not
        if "album_uuid" in self.kwargs:
            # show only one album in the form
            album = get_object_or_404(Album.bmanager.all(), pk=self.kwargs["album_uuid"])
            if not self.request.user.has_perm("change_album", album):
                raise PermissionDenied
            # show the files not in the album in the form
            form.fields["files_to_add"].choices = [
                (bf.pk, bf.pk)
                for bf in BaseFile.bmanager.get_permitted(user=self.request.user)
                if bf not in album.active_files_list
            ]
            form.fields["album"].choices = [(album.pk, album.title)]
            form.initial["album"] = album.pk
        else:
            # we don't have an album_uuid, the form is pre-rendered in FileMultipleActionView and
            # these field choices are only used for validation of the submitted form
            albums = get_objects_for_user(self.request.user, "change_album", klass=Album)
            form.fields["album"].choices = [(a[0], a[1]) for a in albums.values_list("pk", "title")]
            form.fields["files_to_add"].choices = [
                (bf.pk, bf.pk) for bf in BaseFile.bmanager.get_permitted(user=self.request.user)
            ]
        return form  # type: ignore[no-any-return]

    def form_valid(self, form: Form) -> HttpResponse:
        """Add the files and redirect to the album detail page."""
        album = Album.objects.get(pk=form.cleaned_data["album"])
        if not self.request.user.has_perm("change_album", album):
            raise PermissionDenied
        added = album.add_members(*form.cleaned_data["files_to_add"])
        messages.success(
            self.request, f"Added {added} of {len(form.cleaned_data['files_to_add'])} file(s) to album {album.title}"
        )
        return redirect(album)

    def form_invalid(self, form: Form) -> HttpResponse:
        """Return an error message and redirect back to file list."""
        logger.error(form)
        messages.error(self.request, "There was a validation issue with the form:")
        messages.error(self.request, str(form.errors))
        if "fromurl" in form.data:
            return redirect(form.data["fromurl"])
        return redirect(reverse("files:file_list"))


class AlbumRemoveFilesView(LoginRequiredMixin, FormView):  # type: ignore[type-arg]
    """Remove files from an album.

    This view is used by FileMultipleActionView (in which case the form is rendered by
    that view, so files are preselected and only the album needs to be picked) and by
    AlbumDetailView (where album is preselected from the URL and the files need to be picked).
    """

    form_class = AlbumRemoveFilesForm
    template_name = "files_remove_from_album.html"

    def get_form(self, form_class: AlbumAddFilesForm | None = None) -> AlbumAddFilesForm:  # type: ignore[override]
        """Return an instance of the form vith appropriate choices."""
        form = super().get_form()
        # do we have an album_uuid or not
        if "album_uuid" in self.kwargs:
            # show only one album in the form
            album = get_object_or_404(Album.bmanager.all(), pk=self.kwargs["album_uuid"])
            if not self.request.user.has_perm("change_album", album):
                raise PermissionDenied
            # show the files in the album in the form
            form.fields["files_to_remove"].choices = [(bf.pk, bf.pk) for bf in album.active_files_list]
            form.fields["album"].choices = [(album.pk, album.title)]
            form.initial["album"] = album.pk
        else:
            # we don't have an album_uuid, the form is rendered in FileMultipleActionView and
            # these field choices are only used for validation of the submitted form
            albums = get_objects_for_user(self.request.user, "change_album", klass=Album)
            form.fields["album"].choices = [(a[0], a[1]) for a in albums.values_list("pk", "title")]
            form.fields["files_to_remove"].choices = [
                (bf.pk, bf.pk)
                for bf in BaseFile.objects.filter(
                    memberships__album__in=albums, memberships__period__contains=timezone.now()
                )
            ]
        return form  # type: ignore[no-any-return]

    def form_valid(self, form: Form) -> HttpResponse:
        """Add the files and redirect to the album detail page."""
        album = Album.objects.get(pk=form.cleaned_data["album"])
        if not self.request.user.has_perm("change_album", album):
            raise PermissionDenied
        removed = album.remove_members(*form.cleaned_data["files_to_remove"])
        messages.success(
            self.request,
            f"Removed {removed} of {len(form.cleaned_data['files_to_remove'])} file(s) to album {album.title}",
        )
        return redirect(album)

    def form_invalid(self, form: Form) -> HttpResponse:
        """Show an error message and return to fromurl or file list page."""
        logger.error(form)
        messages.error(self.request, "There was a validation issue with the form:")
        messages.error(self.request, str(form.errors))
        if "fromurl" in form.data:
            return redirect(form.data["fromurl"])
        return redirect(reverse("files:file_list"))
