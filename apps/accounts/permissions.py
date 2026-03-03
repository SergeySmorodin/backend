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

        # Определяем владельца объекта
        if hasattr(obj, 'user'):
            is_owner = obj.user == user
        else:
            is_owner = obj == user

        # Админ может всё
        if user.is_staff or user.is_admin or user.is_superuser:
            return True

        # Для безопасных методов (GET, HEAD, OPTIONS) - можно читать свои объекты
        if request.method in permissions.SAFE_METHODS:
            return is_owner

        # Для всех остальных методов (POST, PUT, PATCH, DELETE) - только свои объекты
        return is_owner
