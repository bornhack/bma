from django.urls import path

from files.views import UploadView
from files.views import FilesManageListView

app_name = "files"

urlpatterns = [
    path("manage/", FilesManageListView.as_view(), name="manage"),
    path("upload/", UploadView.as_view(), name="upload"),
]

