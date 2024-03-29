from django.urls import path

from files.views import FileBrowserView
from files.views import FilesApprovalUpdateView
from files.views import FilesManageDeleteView
from files.views import FilesManageDetailView
from files.views import FilesManageEditView
from files.views import FilesManageListView
from files.views import FilesPublishUpdateView
from files.views import FilesUnpublishUpdateView
from files.views import FilesUploadView

app_name = "files"

urlpatterns = [
    path("", FileBrowserView.as_view(), name="browse"),
    path("manage/", FilesManageListView.as_view(), name="manage"),
    path("upload/", FilesUploadView.as_view(), name="upload"),
    path("delete/<pk>/", FilesManageDeleteView.as_view(), name="delete"),
    path("detail/<pk>/", FilesManageDetailView.as_view(), name="detail"),
    path("edit/<pk>/", FilesManageEditView.as_view(), name="edit"),
    path("approve/<pk>/", FilesApprovalUpdateView.as_view(), name="approve"),
    path("publish/<pk>/", FilesPublishUpdateView.as_view(), name="publish"),
    path("unpublish/<pk>/", FilesUnpublishUpdateView.as_view(), name="unpublish"),
]
