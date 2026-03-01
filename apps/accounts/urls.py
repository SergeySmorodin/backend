from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

# URL-паттерны
urlpatterns = [
    # Все маршруты от ViewSet
    path('', include(router.urls)),
]


print("=== Сгенерированные URL для UserViewSet ===")
for url in router.urls:
    print(f"  {url.name}: {url.pattern}")