import logging

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from audios.models import Audio

logger = logging.getLogger("bma")

class AudiosManageListView(LoginRequiredMixin, ListView):
    template_name = "audios_manage_list.html"
    model = Audio

    def get_queryset(self):
        return Audio.objects.filter(owner=self.request.user)
