import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from documents.models import Document

logger = logging.getLogger("bma")


class DocumentsManageListView(LoginRequiredMixin, ListView):
    template_name = "documents_manage_list.html"
    model = Document

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)
