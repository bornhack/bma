import logging

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from documents.models import Document

logger = logging.getLogger("bma")

class DocumentsManageListView(LoginRequiredMixin, ListView):
    template_name = "documents_manage_list.html"
    model = Document

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)
