"""URLs for the files app."""
from django.urls import path

from files.views import FileBrowserView
from files.views import FileDeleteView
from files.views import FileDetailView
from files.views import FileListView
from files.views import FileUpdateView
from files.views import FileUploadView

app_name = "files"

urlpatterns = [
    path("", FileListView.as_view(), name="file_list"),
    path("jsbrowser/", FileBrowserView.as_view(), name="browse"),
    path("upload/", FileUploadView.as_view(), name="upload"),
    path("<pk>/", FileDetailView.as_view(), name="detail"),
    path("delete/<pk>/", FileDeleteView.as_view(), name="delete"),
    path("update/<pk>/", FileUpdateView.as_view(), name="update"),
]
