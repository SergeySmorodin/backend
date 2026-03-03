from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "apps.accounts"

router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="user")

# URL-паттерны
urlpatterns = [
    # Все маршруты от ViewSet
    path("", include(router.urls)),
]
