import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.config.base_test_class.base_test_api_class import BaseTestAPI
from tests.config.data_factories.fake_users_factory import RegularUserFactory

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestAdminAPI(BaseTestAPI):
    """
    Тесты для административных API
    GET /api/accounts/users/me/
    GET /api/accounts/users/
    """

    def test_get_current_user(self, auth_client, regular_user, accounts_me_url):
        """Тест получения информации о текущем пользователе"""
        response = auth_client.get(accounts_me_url)

        self.assert_get_success(response)
        self.assert_user_data(response.data, regular_user)

    def test_list_users_as_admin(self, admin_client, accounts_users_url, regular_user):
        """Тест получения списка пользователей администратором"""
        RegularUserFactory.create_batch(5)

        response = admin_client.get(accounts_users_url)

        self.assert_get_success(response)
        assert len(response.data) >= 6

        user_emails = [user["email"] for user in response.data]
        assert regular_user.email in user_emails

    def test_list_users_as_regular_user(self, auth_client, accounts_users_url):
        """Тест: обычный пользователь может получить список пользователей"""
        RegularUserFactory.create_batch(5)
        response = auth_client.get(accounts_users_url)

        self.assert_get_success(response)

    def test_list_users_unauthorized(self, api_client, accounts_users_url):
        """Тест: неавторизованный пользователь не может получить список"""
        response = api_client.get(accounts_users_url)

        self.assert_permission_denied(response, status.HTTP_403_FORBIDDEN)

    def test_delete_user_as_admin(
        self, admin_client, accounts_detail_url, regular_user
    ):
        """Тест удаления пользователя администратором"""
        response = admin_client.delete(accounts_detail_url(regular_user))

        self.assert_delete_success(response, regular_user.id)

    def test_delete_user_as_regular_user(self, auth_client, accounts_detail_url):
        """Тест: обычный пользователь не может удалить другого пользователя"""
        another_user = RegularUserFactory()
        response = auth_client.delete(accounts_detail_url(another_user))

        self.assert_permission_denied(response)
        assert User.objects.filter(id=another_user.id).exists()

    def test_delete_self_as_regular_user(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """Тест: пользователь не может удалить сам себя"""
        response = auth_client.delete(accounts_detail_url(regular_user))

        self.assert_validation_error(response)
        assert User.objects.filter(id=regular_user.id).exists()

    def test_delete_nonexistent_user(
        self, admin_client, accounts_detail_url, non_existent_user
    ):
        """Тест удаления несуществующего пользователя"""
        response = admin_client.delete(accounts_detail_url(non_existent_user))

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
@pytest.mark.django_db
class TestUserDetailAPI(BaseTestAPI):
    """
    Тесты для операций с конкретным пользователем
    GET /api/accounts/users/{user.id}/
    PUT /api/accounts/users/{user.id}/
    PATCH /api/accounts/users/{user.id}/
    DELETE /api/accounts/users/{user.id}/
    """

    # ============== GET TESTS ==============

    def test_get_user_detail_as_admin(
        self, admin_client, accounts_detail_url, regular_user
    ):
        """
        Админ может получить детальную информацию о любом пользователе
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

    def test_get_user_detail_as_owner(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Пользователь может получить информацию о себе
        GET /api/accounts/users/{user.id}/
        """
        response = auth_client.get(accounts_detail_url(regular_user))

        self.assert_get_success(response)
        self.assert_user_data(response.data, regular_user)
        assert "storage_path" in response.data

    def test_get_user_detail_as_regular_user_other(
        self, auth_client, accounts_detail_url
    ):
        """
        Обычный пользователь не может получить информацию о другом пользователе
        GET /api/accounts/users/{another_user.id}/
        """
        another_user = RegularUserFactory()
        response = auth_client.get(accounts_detail_url(another_user))

        self.assert_permission_denied(response)

    def test_get_nonexistent_user(
        self, admin_client, accounts_detail_url, non_existent_user
    ):
        """
        Запрос несуществующего пользователя
        GET /api/accounts/users/{nonexistent_id}/
        """
        response = admin_client.get(accounts_detail_url(non_existent_user))

        assert response.status_code == status.HTTP_404_NOT_FOUND

        content = response.content.decode()
        assert (
            "not found" in content.lower() in content.lower()
        ), "Ответ должен содержать сообщение о ненайденном ресурсе"

    # ============== PUT TESTS ==============

    def test_put_update_user_as_admin(
        self, admin_client, accounts_detail_url, regular_user
    ):
        """
        Админ может полностью обновить данные пользователя
        PUT /api/accounts/users/{user.id}/
        """
        update_data = {
            "username": "updated_username",
            "email": "updated@example.com",
            "full_name": "Updated Full Name",
            "is_admin": True,
        }

        response = admin_client.put(
            accounts_detail_url(regular_user), update_data, format="json"
        )

        self.assert_update_success(response, update_data, regular_user)

        regular_user.refresh_from_db()
        assert regular_user.is_admin is True

    def test_put_update_user_as_owner(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Пользователь может обновить свои данные (кроме is_admin)
        PUT /api/accounts/users/{user.id}/
        """
        update_data = {
            "username": "my_new_username",
            "email": "my_new@example.com",
            "full_name": "My New Name",
        }

        response = auth_client.put(
            accounts_detail_url(regular_user), update_data, format="json"
        )

        self.assert_update_success(response, update_data, regular_user)

    def test_put_update_other_user_as_regular(self, auth_client, accounts_detail_url):
        """
        Обычный пользователь не может обновить данные другого пользователя
        PUT /api/accounts/users/{another_user.id}/
        """
        another_user = RegularUserFactory()
        update_data = {
            "username": "hacked_username",
            "email": "hacked@example.com",
            "full_name": "Hacked Name",
        }

        response = auth_client.put(
            accounts_detail_url(another_user), update_data, format="json"
        )

        self.assert_permission_denied(response)

        # Проверка, что данные не изменились
        another_user.refresh_from_db()
        assert another_user.username != "hacked_username"

    # ============== PATCH TESTS ==============

    def test_patch_update_user_as_admin(
        self, admin_client, accounts_detail_url, regular_user
    ):
        """
        Админ может частично обновить данные пользователя
        PATCH /api/accounts/users/{user.id}/
        """
        patch_data = {"full_name": "Patched Name", "is_admin": True}

        response = admin_client.patch(
            accounts_detail_url(regular_user), patch_data, format="json"
        )

        self.assert_update_success(response, patch_data, regular_user)

        regular_user.refresh_from_db()
        assert regular_user.full_name == "Patched Name"
        assert regular_user.is_admin is True

    def test_patch_update_user_as_owner(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Пользователь может частично обновить свои данные
        PATCH /api/accounts/users/{user.id}/
        """
        patch_data = {"full_name": "My Patched Name"}

        response = auth_client.patch(
            accounts_detail_url(regular_user), patch_data, format="json"
        )

        self.assert_update_success(response, patch_data, regular_user)

    def test_patch_update_email_to_existing(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Нельзя обновить email на уже существующий
        PATCH /api/accounts/users/{user.id}/
        """
        another_user = RegularUserFactory()

        patch_data = {"email": another_user.email}

        response = auth_client.patch(
            accounts_detail_url(regular_user), patch_data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_patch_update_username_to_existing(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Нельзя обновить username на уже существующий
        PATCH /api/accounts/users/{user.id}/
        """
        another_user = RegularUserFactory()

        patch_data = {"username": another_user.username}

        response = auth_client.patch(
            accounts_detail_url(regular_user), patch_data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_patch_update_user_as_owner(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Пользователь не может обновить is_admin
        PATCH /api/accounts/users/{user.id}/
        """

        update_data = {"is_admin": True}

        response = auth_client.patch(
            accounts_detail_url(regular_user), update_data, format="json"
        )

        # Проверяем, что пришла ошибка 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "is_admin" in response.data
        assert "Только администратор" in str(response.data["is_admin"])

        regular_user.refresh_from_db()
        assert regular_user.is_admin is False

    # ============== PERMISSIONS TESTS ==============

    def test_unauthorized_access(self, api_client, accounts_detail_url, regular_user):
        """
        Неавторизованный пользователь не имеет доступа
        """
        # GET
        response = api_client.get(accounts_detail_url(regular_user))
        self.assert_status(response, status.HTTP_403_FORBIDDEN)  # fixme

        # PUT
        response = api_client.put(accounts_detail_url(regular_user), {}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # PATCH
        response = api_client.patch(
            accounts_detail_url(regular_user), {}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # DELETE
        response = api_client.delete(accounts_detail_url(regular_user))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_do_anything(
        self, admin_client, accounts_detail_url, regular_user
    ):
        """
        Админ имеет полный доступ к любому пользователю
        """
        # GET
        response = admin_client.get(accounts_detail_url(regular_user))
        assert response.status_code == status.HTTP_200_OK

        # PUT
        response = admin_client.put(
            accounts_detail_url(regular_user),
            {
                "username": "admin_updated",
                "email": "admin@test.com",
                "full_name": "Admin Update",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # PATCH
        response = admin_client.patch(
            accounts_detail_url(regular_user),
            {"full_name": "Admin Patch"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # DELETE (но не себя)
        another_user = RegularUserFactory()
        response = admin_client.delete(accounts_detail_url(another_user))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_admin_cannot_delete_self(
        self, admin_client, accounts_detail_url, admin_user
    ):
        """
        Админ не может удалить сам себя
        DELETE /api/accounts/users/{admin.id}/
        """
        response = admin_client.delete(accounts_detail_url(admin_user))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert User.objects.filter(id=admin_user.id).exists()

    def test_regular_user_cannot_delete_self(
        self, auth_client, accounts_detail_url, regular_user
    ):
        """
        Обычный пользователь не может удалить себя (нет прав)
        DELETE /api/accounts/users/{regular_user.id}/
        """
        response = auth_client.delete(accounts_detail_url(regular_user))

        self.assert_validation_error(response)
        assert User.objects.filter(id=regular_user.id).exists()
