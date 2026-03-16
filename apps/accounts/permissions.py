from rest_framework import permissions


class IsAdminOrSelf(permissions.BasePermission):
    """
    Разрешение для работы с пользователями и файлами:
    - GET (список): только админ
    - GET (детальный просмотр): админ или владелец
    - POST (создание): все аутентифицированные
    - PUT/PATCH: админ или владелец
    - DELETE: админ или владелец
    """

    def has_permission(self, request, view):
        """Проверка на уровне view"""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Проверка на уровне объекта
        Вызывается для retrieve/update/destroy
        """
        user = request.user

        # Определяем владельца
        is_owner = (obj == user) or (getattr(obj, 'user', None) == user)

        # Суперпользователь или is_admin=True может всё
        if user.is_superuser or getattr(user, "is_admin", False) or user.is_staff:
            return True

        if view.action == "toggle_admin":
            return False

        # Для безопасных методов (GET) — можно читать свои объекты
        if request.method in permissions.SAFE_METHODS:
            return is_owner

        # Для остальных методов — только свои объекты
        return is_owner
