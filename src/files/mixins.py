from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect

from files.models import StatusChoices


class FilesApprovalMixin(LoginRequiredMixin):

    fields = []
    allowed_approval_status: list
    updated_status: StatusChoices
    error_msg_postfix: str
    success_msg_postfix: str

    def dispatch(self, request, *args, **kwargs):
        """Verify object has allowed status or redirect with error_msg."""
        self.object = self.get_object()
        if self.object.status in self.allowed_approval_status:
            return super().dispatch(request, *args, **kwargs)
        self.error_message()
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, form):
        """Update the status and return with a success_msg"""
        self.object.status = self.updated_status
        self.object.save()
        self.success_message()
        return super().form_valid(form)

    def error_message(self):
        messages.error(
            self.request,
            f"File '{self.object.title}' with status "
            f"'{self.object.get_status_display()}' was {self.error_msg_postfix}!",
        )

    def success_message(self):
        messages.success(
            self.request,
            f"File {self.object.title} was {self.success_msg_postfix}",
        )
