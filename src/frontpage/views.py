import logging

from django.views.generic import TemplateView


logger = logging.getLogger("bma")


class FrontpageTemplateView(TemplateView):

    template_name = "frontpage.html"

