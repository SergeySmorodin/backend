from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestAdminAPI:
    """
    Тесты для административных API
    GET /api/accounts/users/me/
    GET /api/accounts/users/
    GET PUT PATCH DELETE /api/accounts/users/{user.id}/ todo проверить все методы
    """

    def test_get_current_user(self, authenticated_client, regular_user, accounts_me_url):
        """
        Тест получения информации о текущем пользователе
        GET /api/accounts/users/me/
        """

        response = authenticated_client.get(accounts_me_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == regular_user.id
        assert response.data['email'] == regular_user.email
        assert response.data['username'] == regular_user.username
        assert response.data['full_name'] == regular_user.full_name

    def test_list_users_as_admin(self, admin_client, accounts_users_url, regular_user, another_user):
        """
        Тест получения списка пользователей администратором
        GET /api/accounts/users/
        """

        response = admin_client.get(accounts_users_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2
        # Проверяем, что админ тоже в списке
        user_emails = [user['email'] for user in response.data]
        assert regular_user.email in user_emails
        assert another_user.email in user_emails

    def test_list_users_as_regular_user(self, authenticated_client, accounts_users_url):
        """
        Тест получения списка пользователей юзером
        GET /api/accounts/users/
        """

        response = authenticated_client.get(accounts_users_url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_users_unauthorized(self, api_client, accounts_users_url):
        """
        Тест: неавторизованный пользователь не может получить список
        /api/accounts/users/
        """

        response = api_client.get(accounts_users_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_as_admin(self, admin_client, accounts_detail_url, another_user):
        """
        Тест удаления пользователя администратором
        /api/accounts/users/{another_user.id}/
        """

        response = admin_client.delete(
            accounts_detail_url(another_user)
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(id=another_user.id).exists()

    def test_delete_user_as_regular_user(self, authenticated_client, accounts_detail_url, another_user):
        """
        Тест: обычный пользователь не может удалить другого пользователя
        /api/accounts/users/{another_user.id}/
        """

        response = authenticated_client.delete(
            accounts_detail_url(another_user)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert User.objects.filter(id=another_user.id).exists()

    def test_delete_self_as_regular_user(self, authenticated_client, accounts_detail_url, regular_user):
        """
        Тест: пользователь не может удалить сам себя (если не админ)
        /api/accounts/users/{regular_user.id}/
        """

        response = authenticated_client.delete(
            accounts_detail_url(regular_user)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert User.objects.filter(id=regular_user.id).exists()

    def test_delete_nonexistent_user(self, admin_client, accounts_detail_url):
        """
        Тест удаления несуществующего пользователя
        /api/accounts/users/{user.id}
        """

        user = MagicMock(pk=99999)

        response = admin_client.delete(
            accounts_detail_url(user)
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
