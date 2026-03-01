from rest_framework import permissions


class IsAdminOrSelf(permissions.BasePermission):
    """
    Разрешение для работы с пользователями:
    - GET: все аутентифицированные
    - DELETE: только админ (и не себя)
    - PUT/PATCH: админ или сам пользователь
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        if request.method == 'DELETE':
            return (request.user.is_staff or request.user.is_admin or
                    request.user.is_superuser)

        return (request.user.is_staff or request.user.is_admin or
                request.user.is_superuser or obj == request.user)
