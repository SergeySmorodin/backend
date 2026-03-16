import logging

from django.contrib.auth import login, logout
from django.db.models import Count, Sum
from rest_framework import status, permissions, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User
from .permissions import IsAdminOrSelf
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserLoginSerializer,
    UserListSerializer,
    UserUpdateSerializer,
)

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями"""

    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        elif self.action == "list":
            return UserListSerializer
        elif self.action == "retrieve":
            return UserSerializer
        elif self.action == "me":
            return UserSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        """Статистика хранилища для админов"""
        queryset = super().get_queryset()

        if self.request.user and self.request.user.is_admin:
            queryset = queryset.annotate(
                files_count=Count("files"), total_size=Sum("files__size")
            )

        return queryset.order_by("-date_joined")

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """
        Информация о текущем пользователе
        GET /api/accounts/users/me/
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Регистрация нового пользователя
        POST /api/accounts/users/register/
        """
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
                "message": "Регистрация прошла успешно",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """
        Вход в систему
        POST /api/accounts/users/login/
        """
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
                "message": "Вход выполнен успешно",
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def logout(self, request):
        """
        Выход из системы
        POST /api/accounts/users/logout/
        """
        try:
            if hasattr(request.user, "auth_token"):
                request.user.auth_token.delete()
            logout(request)
            return Response({"message": "Выход выполнен успешно"})
        except Exception as e:
            logger.error(f"Ошибка при выходе: {str(e)}")
            return Response(
                {"error": "Ошибка при выходе из системы"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True, methods=["patch"],
        url_path="toggle-admin",
        permission_classes=[IsAdminOrSelf]
    )
    def toggle_admin(self, request, pk=None):
        """Переключение статуса администратора"""

        user = request.user
        target_user = self.get_object()

        if not (user.is_staff or getattr(user, "is_admin", False) or user.is_superuser):
            if target_user != user:
                return Response(
                    {
                        "error": "У вас недостаточно прав для выполнения данного действия."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        if target_user.is_superuser:
            return Response(
                {"error": "Нельзя изменить права суперпользователя"},
                status=status.HTTP_403_FORBIDDEN,
            )

        is_admin = request.data.get(
            "isAdmin", not getattr(target_user, "is_admin", False)
        )
        target_user.is_admin = is_admin
        target_user.save(update_fields=["is_admin"])

        serializer = self.get_serializer(target_user)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Запрещаем удаление самого себя и суперпользователей"""
        user = self.get_object()

        if user == request.user:
            return Response(
                {"error": "Нельзя удалить самого себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_superuser:
            return Response(
                {"error": "Нельзя удалить суперпользователя"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)
