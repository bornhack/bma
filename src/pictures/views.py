import logging

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from pictures.models import Picture

logger = logging.getLogger("bma")

class PicturesManageListView(LoginRequiredMixin, ListView):
    template_name = "pictures_manage_list.html"
    model = Picture

    def get_queryset(self):
        return Picture.objects.filter(owner=self.request.user)
