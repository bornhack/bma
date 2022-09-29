import logging

from django.views.generic import TemplateView

from audios.models import Audio
from documents.models import Document
from pictures.models import Picture
from videos.models import Video


logger = logging.getLogger("bma")


class FrontpageTemplateView(TemplateView):

    template_name = "frontpage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["6_last_pictures"] = self._query_last_6_uploads(Picture)
        context["6_last_videos"] = self._query_last_6_uploads(Video)
        context["6_last_audios"] = self._query_last_6_uploads(Audio)
        context["6_last_documents"] = self._query_last_6_uploads(Document)
        return context

    def _query_last_6_uploads(self, model):
        try:
            return model.objects.all().order_by("created")[:6]
        except model.doesnotexist:
            return ""
