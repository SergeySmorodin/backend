import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.config.base_test_class.base_test_api_class import BaseTestAPI
from tests.config.data_factories.fake_users_factory import RegularUserFactory

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestUserDetailAPI(BaseTestAPI):
    """
    Тесты для операций с конкретным пользователем
    DELETE /api/accounts/users/{user.id}/
    """

    def test_delete_user_as_admin(self, admin_client, accounts_detail_url, regular_user):
        """
        Администратор может удалить другого пользователя
        DELETE /api/accounts/users/{user.id}/
        """
        response = admin_client.delete(accounts_detail_url(regular_user))

        self.assert_delete_success(response, regular_user.id)

    def test_admin_cannot_delete_self(self, admin_client, accounts_detail_url, admin_user):
        """
        Администратор не может удалить сам себя
        DELETE /api/accounts/users/{admin.id}/
        """
        response = admin_client.delete(accounts_detail_url(admin_user))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert User.objects.filter(id=admin_user.id).exists()

    def test_delete_user_as_regular_user(self, auth_client, accounts_detail_url):
        """
        Обычный пользователь не может удалить другого пользователя
        DELETE /api/accounts/users/{another_user.id}/
        """
        another_user = RegularUserFactory()
        response = auth_client.delete(accounts_detail_url(another_user))

        self.assert_permission_denied(response)
        assert User.objects.filter(id=another_user.id).exists()

    def test_delete_self_as_regular_user(self, auth_client, accounts_detail_url, regular_user):
        """
        Обычный пользователь не может удалить сам себя
        DELETE /api/accounts/users/{user.id}/
        """
        response = auth_client.delete(accounts_detail_url(regular_user))

        self.assert_validation_error(response)
        assert User.objects.filter(id=regular_user.id).exists()
        assert User.objects.filter(username=regular_user.username).exists()

    def test_delete_nonexistent_user(self, admin_client, accounts_detail_url, non_existent_user):
        """
        Попытка удалить несуществующего пользователя
        DELETE /api/accounts/users/{nonexistent_id}/
        """
        response = admin_client.delete(accounts_detail_url(non_existent_user))

        assert response.status_code == status.HTTP_404_NOT_FOUND
