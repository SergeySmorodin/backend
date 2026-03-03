import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.config.base_test_class.base_test_api_class import BaseTestAPI

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestAuthAPI(BaseTestAPI):
    """
    Тесты для аутентификации

    POST /api/accounts/users/register/
    POST /api/accounts/users/login/
    POST /api/accounts/users/logout/
    """

    def test_register_user(self, api_client, accounts_register_url, test_user_data):
        """
        Тест регистрации пользователя
        POST /api/accounts/users/register/
        """

        payload = test_user_data

        response = api_client.post(accounts_register_url, payload, format="json")

        self.assert_status(response, status.HTTP_201_CREATED)
        self.assert_response_has_fields(response.data, ["token", "user"])

        # Проверяем данные пользователя
        user_data = response.data["user"]
        self.assert_response_has_fields(user_data, ["id", "email", "username"])
        assert user_data["email"] == payload["email"]
        assert user_data["username"] == payload["username"]

        # Проверяем, что пользователь создан в БД
        assert User.objects.filter(email=payload["email"]).exists()

    def test_register_user_password_mismatch(
        self, api_client, accounts_register_url, test_user_data
    ):
        """
        Тест регистрации с несовпадающими паролями
        POST /api/accounts/users/register/
        """

        payload = test_user_data
        payload["password2"] = "DifferentPass123!"

        response = api_client.post(accounts_register_url, payload, format="json")

        # Используем методы проверки ошибок из базового класса
        self.assert_validation_error(response)

        # Дополнительная проверка наличия ошибки в конкретном поле
        error_fields = response.data.keys()
        assert any(
            field in error_fields for field in ["password", "non_field_errors"]
        ), f"Ожидалась ошибка в полях 'password' или 'non_field_errors', получено: {error_fields}"

    def test_register_user_duplicate_email(
        self, api_client, regular_user, accounts_register_url, test_user_data
    ):
        """
        Тест регистрации с существующим email
        POST /api/accounts/users/register/
        """

        payload = test_user_data
        payload["email"] = regular_user.email  # Существующий email

        response = api_client.post(accounts_register_url, payload, format="json")

        # Проверяем ошибку валидации для поля email
        self.assert_error_response(
            response, status.HTTP_400_BAD_REQUEST, expected_field="email"
        )

    def test_login_user(
        self, api_client, regular_user, accounts_login_url, test_login_data
    ):
        """
        Тест входа в систему
        POST /api/accounts/users/login/
        """

        payload = test_login_data

        response = api_client.post(accounts_login_url, payload, format="json")

        self.assert_status(response, status.HTTP_200_OK)
        self.assert_response_has_fields(response.data, ["token", "user"])

        user_data = response.data["user"]
        self.assert_user_data(user_data, regular_user)
        assert user_data["id"] == regular_user.id

    def test_login_wrong_password(
        self, api_client, regular_user, accounts_login_url, test_login_data
    ):
        """
        Тест входа с неверным паролем
        POST /api/accounts/users/login/
        """

        payload = test_login_data
        payload["password"] = "wrongpass"

        response = api_client.post(accounts_login_url, payload, format="json")

        self.assert_validation_error(response)

    def test_logout(self, auth_client, accounts_logout_url):
        """
        Тест выхода из системы
        POST /api/accounts/users/logout/
        """

        response = auth_client.post(accounts_logout_url)

        self.assert_status(response, status.HTTP_200_OK)
        self.assert_response_has_fields(response.data, ["message"])

        assert response.data["message"] == "Выход выполнен успешно"
