from rest_framework import permissions


class IsAdminOrSelf(permissions.BasePermission):
    """
    Разрешение для работы с пользователями:
    - GET (список): только админ
    - GET (детальный просмотр): админ или сам пользователь
    - PUT/PATCH: админ или сам пользователь
    - DELETE: только админ
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

        if user.is_staff or user.is_admin or user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return obj == user

        if request.method == 'DELETE':
            return False

        return obj == user
