import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from videos.models import Video

logger = logging.getLogger("bma")


class VideoManageListView(LoginRequiredMixin, ListView):
    template_name = "videos_manage_list.html"
    model = Video

    def get_queryset(self):
        return Video.objects.filter(owner=self.request.user)
