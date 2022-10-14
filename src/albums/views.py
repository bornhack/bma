from django.views.generic import TemplateView


class AlbumListTemplateView(TemplateView):
    template_name = "album_list.html"
