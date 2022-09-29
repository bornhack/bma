from django.urls import path

from audios.views import AudiosManageListView

app_name = "audios"

urlpatterns = [
    path("manage/", AudiosManageListView.as_view(), name="manage"),
]

