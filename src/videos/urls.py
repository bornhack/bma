from django.urls import path

from videos.views import VideoManageListView

app_name = "videos"

urlpatterns = [
    path("manage/", VideoManageListView.as_view(), name="manage"),
]

