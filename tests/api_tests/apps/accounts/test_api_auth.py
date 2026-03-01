import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestAuthAPI:
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

        response = api_client.post(
            accounts_register_url,
            payload,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

        assert 'token' in response.data
        assert response.data['user']['email'] == payload['email']
        assert response.data['user']['username'] == payload['username']

        # Проверяем, что пользователь создан в БД
        assert User.objects.filter(email=payload['email']).exists()

    def test_register_user_password_mismatch(self, api_client, accounts_register_url, test_user_data):
        """
        Тест регистрации с несовпадающими паролями
        POST /api/accounts/users/register/
        """

        payload = test_user_data
        payload['password2'] = 'DifferentPass123!'

        response = api_client.post(
            accounts_register_url,
            payload,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data or 'non_field_errors' in response.data

    def test_register_user_duplicate_email(self, api_client, regular_user, accounts_register_url, test_user_data):
        """
        Тест регистрации с существующим email
        POST /api/accounts/users/register/
        """

        payload = test_user_data
        payload['email'] = regular_user.email,  # Существующий email

        response = api_client.post(
            accounts_register_url,
            payload,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_login_user(self, api_client, regular_user, accounts_login_url, test_login_data):
        """
        Тест входа в систему
        POST /api/accounts/users/login/
        """

        payload = test_login_data

        response = api_client.post(
            accounts_login_url,
            payload,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert response.data['user']['id'] == regular_user.id

    def test_login_wrong_password(self, api_client, regular_user, accounts_login_url, test_login_data):
        """
        Тест входа с неверным паролем
        POST /api/accounts/users/login/
        """

        payload = test_login_data
        payload['password'] = 'wrongpass'

        response = api_client.post(
            accounts_login_url,
            payload,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout(self, auth_client, accounts_logout_url):
        """
        Тест выхода из системы
        POST /api/accounts/users/logout/
        """

        response = auth_client.post(accounts_logout_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Выход выполнен успешно'
