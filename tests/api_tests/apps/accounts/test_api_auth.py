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

    def test_register_user(self, api_client, accounts_register_url):
        """
        Тест регистрации пользователя
        POST /api/accounts/users/register/
        """

        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'full_name': 'New Test User'
        }

        response = api_client.post(
            accounts_register_url,
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert response.data['user']['email'] == data['email']
        assert response.data['user']['username'] == data['username']

        # Проверяем, что пользователь создан в БД
        assert User.objects.filter(email=data['email']).exists()

    def test_register_user_password_mismatch(self, api_client, accounts_register_url):
        """
        Тест регистрации с несовпадающими паролями
        POST /api/accounts/users/register/
        """

        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'TestPass123!',
            'password2': 'DifferentPass123!',
            'full_name': 'New Test User'
        }

        response = api_client.post(
            accounts_register_url,
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data or 'non_field_errors' in response.data

    def test_register_user_duplicate_email(self, api_client, regular_user, accounts_register_url):
        """
        Тест регистрации с существующим email
        POST /api/accounts/users/register/
        """

        data = {
            'username': 'anotheruser',
            'email': regular_user.email,  # Существующий email
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'full_name': 'Another User'
        }

        response = api_client.post(
            accounts_register_url,
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_login_user(self, api_client, regular_user, accounts_login_url):
        """
        Тест входа в систему
        POST /api/accounts/users/login/
        """

        data = {
            'username': regular_user.username,
            'password': 'testpass123'
        }

        response = api_client.post(
            accounts_login_url,
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert response.data['user']['id'] == regular_user.id

    def test_login_wrong_password(self, api_client, regular_user, accounts_login_url):
        """
        Тест входа с неверным паролем
        POST /api/accounts/users/login/
        """

        data = {
            'username': regular_user.username,
            'password': 'wrongpass'
        }

        response = api_client.post(
            accounts_login_url,
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout(self, authenticated_client, accounts_logout_url):
        """
        Тест выхода из системы
        POST /api/accounts/users/logout/
        """

        response = authenticated_client.post(accounts_logout_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Выход выполнен успешно'
