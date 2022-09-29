from django.urls import path

from frontpage.views import FrontpageTemplateView

app_name = "frontpage"

urlpatterns = [
    path("", FrontpageTemplateView.as_view(), name="frontpage"),
]

