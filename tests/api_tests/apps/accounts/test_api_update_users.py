import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.config.base_test_class.base_test_api_class import BaseTestAPI
from tests.config.data_factories.fake_users_factory import RegularUserFactory

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestUserPutDetailAPI(BaseTestAPI):
    """
    Тесты для операций с конкретным пользователем
    PUT /api/accounts/users/{user.id}/
    """

    def test_put_update_user_as_admin(
        self, admin_client, accounts_detail_url, regular_user, put_data
    ):
        """
        Администратор может полностью обновить данные любого пользователя
        PUT /api/accounts/users/{user.id}/
        """
        update_data = put_data
        update_data.update({"is_admin": True})

        response = admin_client.put(
            accounts_detail_url(regular_user), update_data, format="json"
        )

        self.assert_update_success(response, update_data, regular_user)

        regular_user.refresh_from_db()
        assert regular_user.is_admin is True

    def test_put_update_user_as_owner(
        self, auth_client, accounts_detail_url, regular_user, put_data
    ):
        """
        Пользователь может полностью обновить свои данные (кроме is_admin)
        PUT /api/accounts/users/{user.id}/
        """
        response = auth_client.put(
            accounts_detail_url(regular_user), put_data, format="json"
        )

        self.assert_update_success(response, put_data, regular_user)

    def test_put_update_other_user_as_regular(
        self, auth_client, accounts_detail_url, put_data
    ):
        """
        Обычный пользователь не может обновить данные другого пользователя
        PUT /api/accounts/users/{another_user.id}/
        """
        another_user = RegularUserFactory()

        response = auth_client.put(
            accounts_detail_url(another_user), put_data, format="json"
        )

        self.assert_permission_denied(response)

        # Проверка, что данные не изменились
        another_user.refresh_from_db()
        assert another_user.username != put_data["username"]


@pytest.mark.api
@pytest.mark.django_db
class TestUserPatchDetailAPI(BaseTestAPI):
    """
    Тесты для операций с конкретным пользователем
    PATCH /api/accounts/users/{user.id}/
    """

    def test_patch_update_user_as_admin(
        self, admin_client, accounts_detail_url, regular_user, patch_data
    ):
        """
        Администратор может частично обновить данные любого пользователя
        PATCH /api/accounts/users/{user.id}/
        """
        update_data = patch_data
        update_data.update({"is_admin": True})

        response = admin_client.patch(
            accounts_detail_url(regular_user), update_data, format="json"
        )

        self.assert_update_success(response, update_data, regular_user)

        regular_user.refresh_from_db()
        assert regular_user.full_name == patch_data["full_name"]
        assert regular_user.is_admin is True

    def test_patch_update_user_as_owner(
        self, auth_client, accounts_detail_url, regular_user, patch_data
    ):
        """
        Пользователь может частично обновить свои данные
        PATCH /api/accounts/users/{user.id}/
        """
        response = auth_client.patch(
            accounts_detail_url(regular_user), patch_data, format="json"
        )

        self.assert_update_success(response, patch_data, regular_user)

    def test_patch_update_user_cannot_change_is_admin(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Обычный пользователь не может изменить свой статус is_admin
        PATCH /api/accounts/users/{user.id}/
        """
        response = auth_client.patch(
            accounts_detail_url(regular_user), {"is_admin": True}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "is_admin" in response.data
        assert "Только администратор" in str(response.data["is_admin"])

        regular_user.refresh_from_db()
        assert regular_user.is_admin is False

    def test_patch_update_email_to_existing(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Нельзя обновить email на уже существующий в системе
        PATCH /api/accounts/users/{user.id}/
        """
        another_user = RegularUserFactory()

        response = auth_client.patch(
            accounts_detail_url(regular_user),
            {"email": another_user.email},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_patch_update_username_to_existing(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Нельзя обновить username на уже существующий в системе
        PATCH /api/accounts/users/{user.id}/
        """
        another_user = RegularUserFactory()

        response = auth_client.patch(
            accounts_detail_url(regular_user),
            {"username": another_user.username},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data
