import shutil
import tempfile
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from tests.data_factories.fake_users_factory import RegularUserFactory, AdminUserFactory

User = get_user_model()

_ORIGINAL_MEDIA_ROOT = None

pytest_plugins = [
    "tests.api_tests.endpoints.accounts_url",
    "tests.api_tests.endpoints.storage_url",
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


@pytest.fixture
def test_file():
    """Фикстура для тестового файла"""

    file_content = b"Test file content"
    test_file = SimpleUploadedFile(
        "test.txt",
        file_content,
        content_type="text/plain"
    )
    return test_file


@pytest.fixture
def test_image():
    """Фикстура для тестового изображения"""

    file_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    test_image = SimpleUploadedFile(
        "test.gif",
        file_content,
        content_type="image/gif"
    )
    return test_image
