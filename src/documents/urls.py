from django.urls import path

from documents.views import DocumentsManageListView

app_name = "documents"

urlpatterns = [
    path("manage/", DocumentsManageListView.as_view(), name="manage"),
]
