from django.urls import path

from files.views import FilesManageDeleteView
from files.views import FilesManageDetailView
from files.views import FilesManageListView
from files.views import FilesUploadView

app_name = "files"

urlpatterns = [
    path("manage/", FilesManageListView.as_view(), name="manage"),
    path("upload/", FilesUploadView.as_view(), name="upload"),
    path("delete/<pk>", FilesManageDeleteView.as_view(), name="delete"),
    path("detail/<pk>", FilesManageDetailView.as_view(), name="detail"),
]
