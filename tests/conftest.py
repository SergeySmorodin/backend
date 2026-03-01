import shutil
import tempfile
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

User = get_user_model()

_ORIGINAL_MEDIA_ROOT = None

pytest_plugins = [
    "tests.api_tests.endpoints.accounts_url"
]


@pytest.fixture(scope='session', autouse=True)
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
    """Фикстура для API клиента"""

    return APIClient()


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """Фикстура для авторизованного клиента"""

    token, created = Token.objects.get_or_create(user=regular_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Фикстура для авторизованного админ-клиента"""

    token, created = Token.objects.get_or_create(user=admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def regular_user(db):
    """Фикстура для обычного пользователя"""

    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        full_name='Test User'
    )
    return user


@pytest.fixture
def another_user(db):
    """Фикстура для другого обычного пользователя"""

    user = User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='testpass123',
        full_name='Another User'
    )
    return user


@pytest.fixture
def admin_user(db):
    """Фикстура для администратора"""

    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        full_name='Admin User'
    )
    user.is_admin = True
    user.save()
    return user


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


