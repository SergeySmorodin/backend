import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Тесты для модели пользователя"""

    def test_create_user(self):
        """Тест создания обычного пользователя"""
        user = User.objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password="testpass123",
            full_name="New User",
        )

        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.check_password("testpass123")
        assert not user.is_admin
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        """Тест создания суперпользователя"""
        admin = User.objects.create_superuser(
            username="admin2",
            email="admin2@example.com",
            password="adminpass123",
            full_name="Admin User 2",
        )

        assert admin.is_superuser
        assert admin.is_staff
        assert not admin.is_admin

    def test_unique_email(self):
        """Тест уникальности email"""
        User.objects.create_user(
            username="user1", email="same@example.com", password="testpass123"
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="user2", email="same@example.com", password="testpass123"
            )

    def test_user_str_method(self, regular_user):
        """Тест строкового представления пользователя"""

        assert str(regular_user) == regular_user.full_name or regular_user.username
