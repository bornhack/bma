"""URL Configuration for the galleries app."""
from django.urls import include
from django.urls import path

from .views import GalleryManageCreateView
from .views import GalleryManageDetailView
from .views import GalleryManageListView
from .views import GalleryManagePublishView
from .views import GalleryManageUnpublishView
from .views import GalleryManageUpdateView
from .views import GalleryPublicDetailView
from .views import GalleryPublicListView

app_name = "galleries"
urlpatterns = [
    path(
        "manage/",
        include(
            [
                path("", GalleryManageListView.as_view(), name="gallery_manage_list"),
                path(
                    "create/",
                    GalleryManageCreateView.as_view(),
                    name="gallery_manage_create",
                ),
                path(
                    "<slug:slug>/",
                    include(
                        [
                            path(
                                "",
                                GalleryManageDetailView.as_view(),
                                name="gallery_manage_detail",
                            ),
                            path(
                                "update/",
                                GalleryManageUpdateView.as_view(),
                                name="gallery_manage_update",
                            ),
                            path(
                                "publish/",
                                GalleryManagePublishView.as_view(),
                                name="gallery_manage_publish",
                            ),
                            path(
                                "unpublish/",
                                GalleryManageUnpublishView.as_view(),
                                name="gallery_manage_unpublish",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    path("", GalleryPublicListView.as_view(), name="gallery_public_list"),
    path(
        "<slug:slug>/",
        include(
            [
                path(
                    "",
                    GalleryPublicDetailView.as_view(),
                    name="gallery_public_detail",
                ),
            ],
        ),
    ),
]
