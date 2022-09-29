from django.urls import path

from files.views import FilesUploadView
from files.views import FilesManageListView

app_name = "files"

urlpatterns = [
    path("manage/", FilesManageListView.as_view(), name="manage"),
    path("upload/", FilesUploadView.as_view(), name="upload"),
]

