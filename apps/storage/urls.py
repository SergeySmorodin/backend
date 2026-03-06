from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "apps.storage"

router = DefaultRouter()
router.register(r"", views.FileViewSet, basename="file")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "share/<str:share_link>/",
        views.FileShareDownloadView.as_view(),
        name="file-share-download"
    ),
]
