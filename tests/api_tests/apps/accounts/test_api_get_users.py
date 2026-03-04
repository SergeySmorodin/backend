import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.config.base_test_class.base_test_api_class import BaseTestAPI
from tests.config.data_factories.fake_users_factory import RegularUserFactory

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestUserListAPI(BaseTestAPI):
    """
    Тесты для списка пользователей
    GET /api/accounts/users/
    GET /api/accounts/users/me/
    """

    def test_list_users_as_admin(self, admin_client, accounts_users_url, regular_user):
        """
        Администратор может получить список всех пользователей
        GET /api/accounts/users/
        """
        RegularUserFactory.create_batch(5)

        response = admin_client.get(accounts_users_url)

        self.assert_get_success(response)
        assert len(response.data) >= 6

        user_emails = [user["email"] for user in response.data]
        assert regular_user.email in user_emails

    def test_list_users_as_regular_user(self, auth_client, accounts_users_url):
        """
        Обычный пользователь может получить список пользователей
        GET /api/accounts/users/
        """
        RegularUserFactory.create_batch(5)
        response = auth_client.get(accounts_users_url)

        self.assert_get_success(response)

    def test_list_users_unauthorized(self, api_client, accounts_users_url):
        """
        Неавторизованный пользователь не может получить список пользователей
        GET /api/accounts/users/
        """
        response = api_client.get(accounts_users_url)

        self.assert_permission_denied(response, status.HTTP_403_FORBIDDEN)

    def test_get_current_user(self, auth_client, regular_user, accounts_me_url):
        """
        Пользователь может получить информацию о себе
        GET /api/accounts/users/me/
        """
        response = auth_client.get(accounts_me_url)

        self.assert_get_success(response)
        self.assert_user_data(response.data, regular_user)


@pytest.mark.api
@pytest.mark.django_db
class TestUserGetDetailAPI(BaseTestAPI):
    """
    Тесты для операций с конкретным пользователем
    GET /api/accounts/users/{user.id}/
    """

    def test_get_user_detail_as_admin(self, admin_client, accounts_detail_url, regular_user):
        """
        Администратор может получить детальную информацию о любом пользователе
        GET /api/accounts/users/{user.id}/
        """
        response = admin_client.get(accounts_detail_url(regular_user))

        self.assert_get_success(response)
        self.assert_user_data(
            response.data,
            regular_user,
            ["id", "username", "email", "full_name", "is_admin"],
        )

        # Дополнительные поля для админа
        assert "storage_path" in response.data
        assert "date_joined" in response.data

    def test_get_user_detail_as_owner(self, auth_client, accounts_detail_url, regular_user):
        """
        Пользователь может получить информацию о себе через detail URL
        GET /api/accounts/users/{user.id}/
        """
        response = auth_client.get(accounts_detail_url(regular_user))

        self.assert_get_success(response)
        self.assert_user_data(response.data, regular_user)
        assert "storage_path" in response.data

    def test_get_user_detail_as_regular_user_other(self, auth_client, accounts_detail_url):
        """
        Обычный пользователь не может получить информацию о другом пользователе
        GET /api/accounts/users/{another_user.id}/
        """
        another_user = RegularUserFactory()
        response = auth_client.get(accounts_detail_url(another_user))

        self.assert_permission_denied(response)

    def test_get_nonexistent_user(self, admin_client, accounts_detail_url, non_existent_user):
        """
        Запрос несуществующего пользователя возвращает 404
        GET /api/accounts/users/{nonexistent_id}/
        """
        response = admin_client.get(accounts_detail_url(non_existent_user))

        assert response.status_code == status.HTTP_404_NOT_FOUND

        content = response.content.decode()
        assert (
                "not found" in content.lower()
        ), "Ответ должен содержать сообщение о ненайденном ресурсе"
