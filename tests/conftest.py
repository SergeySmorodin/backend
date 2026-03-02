import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from tests.config.data_factories.fake_users_factory import RegularUserFactory, AdminUserFactory

User = get_user_model()

_ORIGINAL_MEDIA_ROOT = None

pytest_plugins = [
    "tests.api_tests.endpoints.accounts_url",
    "tests.api_tests.endpoints.storage_url",
    "tests.config.data_factories.fake_files_factory",
    "tests.config.data_factories.fake_users_factory",
]


@pytest.fixture(scope='function', autouse=True)
def temp_media_root():
    """Создает временную медиа-директорию для всех тестов"""

    global _ORIGINAL_MEDIA_ROOT

    temp_dir = tempfile.mkdtemp()
    print(f"Тестовая директория: {temp_dir}")
    _ORIGINAL_MEDIA_ROOT = settings.MEDIA_ROOT

    if hasattr(_ORIGINAL_MEDIA_ROOT, 'joinpath'):
        settings.MEDIA_ROOT = Path(temp_dir)
    else:
        settings.MEDIA_ROOT = temp_dir

    yield temp_dir

    shutil.rmtree(temp_dir, ignore_errors=True)
    settings.MEDIA_ROOT = _ORIGINAL_MEDIA_ROOT


@pytest.fixture
def api_client():
    """API клиент"""

    return APIClient()


@pytest.fixture
def regular_user():
    return RegularUserFactory()


@pytest.fixture
def admin_user():
    return AdminUserFactory()


@pytest.fixture
def non_existent_user():
    """Фикстура для несуществующего user"""
    user = MagicMock(pk=9999)
    return user


@pytest.fixture
def auth_client(api_client, regular_user):
    """Авторизованный клиент"""

    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Клиент с авторизацией администратора"""

    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def user_token(regular_user):
    """Фикстура для токена обычного пользователя"""

    token, created = Token.objects.get_or_create(user=regular_user)
    return token


@pytest.fixture
def admin_token(admin_user):
    """Фикстура для токена администратора"""

    token, created = Token.objects.get_or_create(user=admin_user)
    return token
