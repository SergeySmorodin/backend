import pytest
from django.contrib.auth import get_user_model

from tests.config.base_test_class.base_test_api_class import BaseTestAPI

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestUsersToggleAdminApiTestAPI(BaseTestAPI):
    """
    Тесты для эндпоинта toggle-admin (переключение прав администратора)
    """

    def test_toggle_admin_success_by_superuser(self, admin_client, accounts_toggle_admin_url, regular_user):
        """
        Суперпользователь может переключать статус администратора
        PATCH /api/accounts/users/${userId}/toggle-admin/
        """

        assert regular_user.is_admin is False

        response = admin_client.patch(
            accounts_toggle_admin_url(regular_user)
        )

        self.assert_status(response, 200)
        self.assert_response_has_fields(response.data, ["id", "username", "is_admin"])

        assert response.data["is_admin"] is True

        # проверяем в БД
        regular_user.refresh_from_db()
        assert regular_user.is_admin is True

        # Возвращаем обратно
        response = admin_client.patch(
            accounts_toggle_admin_url(regular_user)
        )

        self.assert_status(response, 200)
        assert response.data["is_admin"] is False

        regular_user.refresh_from_db()
        assert regular_user.is_admin is False

    def test_toggle_admin_forbidden_for_regular_user(self, auth_client, accounts_toggle_admin_url, regular_user):
        """
        Обычный пользователь НЕ может переключать статус администратора
        PATCH /api/accounts/users/${userId}/toggle-admin/
        """

        response = auth_client.patch(
            accounts_toggle_admin_url(regular_user)
        )

        self.assert_permission_denied(response, 403)

    def test_toggle_admin_unauthorized(self, api_client, accounts_toggle_admin_url, regular_user):
        """
        Неавторизованный пользователь не может переключать статус
        PATCH /api/accounts/users/${userId}/toggle-admin/
        """

        response = api_client.patch(
            accounts_toggle_admin_url(regular_user)
        )

        self.assert_error_response(
            response, 403, expected_message="Учетные данные не были предоставлены."
        )

    def test_toggle_admin_not_found(self, admin_client, non_existent_user, accounts_toggle_admin_url):
        """
        Переключение статуса несуществующего пользователя
        PATCH /api/accounts/users/${userId}/toggle-admin/
        """
        user = non_existent_user

        response = admin_client.patch(
            accounts_toggle_admin_url(user)
        )

        self.assert_not_found(response)

    def test_toggle_admin_cannot_demote_self(self, admin_client, accounts_toggle_admin_url, admin_user):
        """
        Админ не может снять права сам с себя через этот эндпоинт
        PATCH /api/accounts/users/${userId}/toggle-admin/
        """

        response = admin_client.patch(
            accounts_toggle_admin_url(admin_user)
        )

        self.assert_error_response(
            response, 403, expected_message="Нельзя изменить права суперпользователя"
        )
