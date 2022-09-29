from django.urls import path

from pictures.views import PicturesManageListView

app_name = "pictures"

urlpatterns = [
    path("manage/", PicturesManageListView.as_view(), name="manage"),
]

