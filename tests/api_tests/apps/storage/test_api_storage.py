from pprint import pprint
from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestStorageAPI:
    """
    Тесты для работы с файлами через API

    """

    def test_get_current_user(self, authenticated_client, regular_user, storage_url):
        """
        Тест получения всех файлов
        GET /api/storage/
        """

        response = authenticated_client.get(storage_url)
        pprint(response.json())

        assert response.status_code == status.HTTP_200_OK



