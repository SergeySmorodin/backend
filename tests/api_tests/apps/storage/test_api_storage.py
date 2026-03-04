import os
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.storage.models import UserFile
from tests.config.base_test_class.base_test_api_class import BaseTestAPI
from tests.config.data_factories.fake_files_factory import UserFileFactory
from tests.config.data_factories.fake_users_factory import RegularUserFactory
from tests.conftest import regular_user

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestFileAPIPermissions(BaseTestAPI):
    """Тесты прав доступа к API файлов"""

    def test_unauthenticated_cannot_access_files(self, api_client, storage_url):
        """
        Неавторизованный пользователь не может получить список файлов
        GET /api/storage/
        """
        response = api_client.get(storage_url)
        self.assert_status(response, status.HTTP_403_FORBIDDEN)

    def test_authenticated_can_access_own_files(
        self, auth_client, regular_user, storage_url
    ):
        """
        Авторизованный пользователь может получить свои файлы
        GET /api/storage/
        """
        test_file = UserFileFactory(user=regular_user)

        response = auth_client.get(storage_url)

        self.assert_get_success(response)
        assert len(response.data) == 1
        assert response.data[0]["original_name"] == test_file.original_name
        assert response.data[0]["owner"]["id"] == regular_user.id

    def test_user_cannot_access_others_files(self, auth_client, storage_url):
        """
        Пользователь не может видеть файлы других пользователей
        GET /api/storage/
        """
        another_user = RegularUserFactory()
        UserFileFactory(user=another_user)

        response = auth_client.get(storage_url)

        self.assert_get_success(response)
        assert len(response.data) == 0  # Не видит чужие файлы

    def test_admin_can_access_all_files(self, admin_client, regular_user, storage_url):
        """
        Администратор может видеть файлы всех пользователей
        GET /api/storage/
        """
        another_user = RegularUserFactory()
        UserFileFactory(user=regular_user, original_name="user1_file.txt")
        UserFileFactory(user=another_user, original_name="user2_file.txt")

        response = admin_client.get(storage_url)

        self.assert_get_success(response)
        assert len(response.data) == 2

    def test_admin_can_filter_by_user_id(self, admin_client, regular_user, storage_url):
        """
        Администратор может фильтровать файлы по user_id
        GET /api/storage/?user_id={user_id}
        """
        another_user = RegularUserFactory()
        user1_file = UserFileFactory(user=regular_user, original_name="user1_file.txt")
        UserFileFactory(user=another_user, original_name="user2_file.txt")

        response = admin_client.get(f"{storage_url}?user_id={regular_user.id}")

        self.assert_get_success(response)
        assert len(response.data) == 1
        assert response.data[0]["original_name"] == user1_file.original_name


@pytest.mark.api
@pytest.mark.django_db
class TestFileUploadAPI(BaseTestAPI):
    """Тесты загрузки файлов"""

    def test_upload_file(self, auth_client, regular_user, storage_url, text_file):
        """
        Тест загрузки файла
        POST /api/storage/
        """
        # Получаем реальный размер файла
        text_file.seek(0, os.SEEK_END)
        file_size = text_file.tell()
        text_file.seek(0)

        response = auth_client.post(
            storage_url,
            {
                "file": text_file,
                "comment": "Test comment",
                "original_name": text_file.name,
            },
            format="multipart",
        )

        expected_data = {
            "original_name": text_file.name,
            "size": file_size,
            "comment": "Test comment",
        }

        # Проверяем ответ
        self.assert_create_success(response)
        self.assert_response_equals(response, expected_data, ignore_fields=["id"])

        # Проверяем наличие ID в ответе
        response_data = response.json()
        assert "id" in response_data

        # Проверяем создание в БД
        assert UserFile.objects.filter(user=regular_user).count() == 1
        file_obj = UserFile.objects.get(id=response_data["id"])
        assert os.path.exists(file_obj.full_path)
        assert file_obj.user.id == regular_user.id
        assert file_obj.size == file_size

    def test_upload_file_without_comment(self, auth_client, storage_url, text_file):
        """
        Тест загрузки файла без комментария
        POST /api/storage/
        """
        response = auth_client.post(
            storage_url,
            {
                "file": text_file,
                "original_name": text_file.name,
            },
            format="multipart",
        )

        self.assert_create_success(response)
        assert response.data["comment"] == ""

    def test_upload_file_too_large(
        self, auth_client, storage_url, settings, test_file_factory
    ):
        """
        Тест загрузки слишком большого файла
        POST /api/storage/
        """

        # Устанавливаем маленький лимит
        settings.STORAGE_SETTINGS["MAX_FILE_SIZE"] = 10  # 10 байт

        # Создаем большой файл через фабрику
        large_file = test_file_factory(
            "binary", filename="large.bin", size_kb=1
        )  # 1KB > 10 байт

        response = auth_client.post(
            storage_url, {"file": large_file}, format="multipart"
        )

        self.assert_validation_error(response)


@pytest.mark.api
@pytest.mark.django_db
class TestFileUpdateAPI(BaseTestAPI):
    """Тесты обновления файлов"""

    def test_update_file_comment(self, auth_client, regular_user, storage_detail_url):
        """
        Тест обновления комментария к файлу
        PATCH /api/storage/{file.id}/
        """
        file = UserFileFactory(user=regular_user, comment="Old comment")

        url = storage_detail_url(file)
        data = {"comment": "New comment"}

        response = auth_client.patch(url, data, format="multipart")

        self.assert_update_success(response, data, file, fields_to_check=["comment"])

    def test_rename_file(self, auth_client, regular_user, storage_detail_url):
        """
        Тест переименования файла
        PATCH /api/storage/{file.id}/
        """
        file = UserFileFactory(user=regular_user, original_name="old_name.txt")

        data = {"original_name": "new_name.txt"}

        response = auth_client.patch(storage_detail_url(file), data, format="multipart")

        self.assert_update_success(
            response, data, file, fields_to_check=["original_name"]
        )

    def test_cannot_update_others_file(self, auth_client, storage_detail_url):
        """
        Пользователь не может обновить чужой файл
        PATCH /api/storage/{file.id}/
        """
        another_user = RegularUserFactory()
        file = UserFileFactory(user=another_user)

        response = auth_client.patch(
            storage_detail_url(file), {"comment": "Hacked comment"}, format="multipart"
        )

        self.assert_permission_denied(
            response, expected_status=status.HTTP_404_NOT_FOUND
        )


@pytest.mark.api
@pytest.mark.django_db
class TestFileDeleteAPI(BaseTestAPI):
    """Тесты удаления файлов"""

    def test_delete_file_admin(self, admin_client, regular_user, storage_detail_url):
        """
        Тест удаления файла админом
        DELETE /api/storage/{file.id}/
        """
        file = UserFileFactory(user=regular_user, create_file=True)

        # Проверяем, что файл создан
        assert os.path.exists(
            file.full_path
        ), f"Файл не создан на диске: {file.full_path}"

        url = storage_detail_url(file)

        response = admin_client.delete(url)

        # Проверяем успешное удаление
        self.assert_delete_success(response, file.id, UserFile)

    def test_delete_file(self, auth_client, regular_user, storage_detail_url):
        """
        Тест удаления своего файла юзером
        DELETE /api/storage/{file.id}/
        """
        file = UserFileFactory(user=regular_user, create_file=True)

        url = storage_detail_url(file)
        response = auth_client.delete(url)

        self.assert_delete_success(response, file.id, UserFile)
        assert not os.path.exists(file.full_path)  # Физический файл удален

    def test_delete_file_removes_empty_dirs(
        self, auth_client, regular_user, storage_detail_url, temp_media_root
    ):
        """
        Тест удаления пустых директорий при удалении файла
        DELETE /api/storage/{file.id}/
        """
        # Создаем файл во вложенной директории
        nested_path = os.path.join("user_files", "subdir", "nested", "test.txt")
        file = UserFileFactory(
            user=regular_user,
            original_name="test.txt",
            file_path=nested_path,
            create_file=True,
        )

        url = storage_detail_url(file)
        response = auth_client.delete(url)

        self.assert_delete_success(response, file.id, UserFile)

        # Проверяем, что вложенные пустые директории удалены
        assert not os.path.exists(
            os.path.join(temp_media_root, "user_files", "subdir", "nested")
        )
        assert not os.path.exists(os.path.join(temp_media_root, "user_files", "subdir"))

        # Проверяем, что корневая директория user_files существует
        assert os.path.exists(os.path.join(temp_media_root, "user_files"))

    def test_cannot_delete_others_file(self, auth_client, storage_detail_url):
        """
        Пользователь не может удалить чужой файл
        DELETE /api/storage/{file.id}/
        """
        another_user = RegularUserFactory()
        file = UserFileFactory(user=another_user, create_file=True)

        url = storage_detail_url(file)
        response = auth_client.delete(url)

        self.assert_permission_denied(
            response, expected_status=status.HTTP_404_NOT_FOUND
        )
        assert UserFile.objects.filter(id=file.id).exists()
        assert os.path.exists(file.full_path)  # Физический файл должен остаться


@pytest.mark.api
@pytest.mark.django_db
class TestFileDownloadAPI(BaseTestAPI):
    """Тесты скачивания файлов"""

    def test_download_file(self, auth_client, regular_user, storage_download_url):
        """
        Тест скачивания файла
        GET /api/storage/{file.id}/download/
        """
        file = UserFileFactory(
            user=regular_user,
            original_name="test.txt",
            create_file="test download content",
        )

        url = storage_download_url(file)
        response = auth_client.get(url)

        self.assert_status(response, status.HTTP_200_OK)
        assert (
            response.headers["Content-Disposition"]
            == f'attachment; filename="{file.original_name}"'
        )

        # Для FileResponse используем streaming_content
        content = b"".join(response.streaming_content)
        assert content == b"test download content"

    def test_view_file_inline(
        self, auth_client, regular_user, storage_view_url, image_file
    ):
        """
        Тест просмотра файла в браузере
        GET /api/storage/{file.id}/view/
        """
        file_content = image_file.read()
        image_file.seek(0)

        file = UserFileFactory(
            user=regular_user, original_name="test.jpg", create_file=file_content
        )

        url = storage_view_url(file)
        response = auth_client.get(url)

        self.assert_status(response, status.HTTP_200_OK)
        assert response.headers["Content-Disposition"].startswith("inline")
        assert "image/" in response.headers["Content-Type"]

    def test_download_nonexistent_file(
        self, auth_client, regular_user, storage_download_url
    ):
        """
        Тест скачивания несуществующего файла
        GET /api/storage/{file.id}/download/
        """
        file = UserFileFactory(
            user=regular_user,
            file_path="user_files/nonexistent.txt",
            create_file=False,  # Не создаем физический файл
        )

        url = storage_download_url(file)
        response = auth_client.get(url)

        self.assert_not_found(response)
        assert "Файл не найден" in response.data["error"]


@pytest.mark.api
@pytest.mark.django_db
class TestFileShareAPI(BaseTestAPI):
    """Тесты создания и использования ссылок"""

    def test_create_share_link(self, auth_client, regular_user, storage_share_url):
        """
        Тест создания ссылки для общего доступа
        POST /api/storage/{file.id}/share/
        """
        file = UserFileFactory(user=regular_user, share_token=None)  # Нет токена

        url = storage_share_url(file)
        response = auth_client.post(url)

        self.assert_status(response, status.HTTP_200_OK)
        assert "share_token" in response.data
        assert "share_url" in response.data
        assert response.data["share_token"] is not None

        file.refresh_from_db()
        assert file.share_token is not None
        assert file.share_token_created is not None

    def test_revoke_share_link(
        self, auth_client, regular_user, storage_revoke_share_url
    ):
        """
        Тест отзыва ссылки для общего доступа
        DELETE /api/storage/{file.id}/revoke_share/
        """
        file = UserFileFactory(user=regular_user, share_token="test_token_123")

        url = storage_revoke_share_url(file)
        response = auth_client.delete(url)

        self.assert_status(response, status.HTTP_204_NO_CONTENT)

        file.refresh_from_db()
        assert file.share_token is None
        assert file.share_token_created is None

    def test_regenerate_share_link(self, auth_client, regular_user, storage_share_url):
        """
        Тест обновления ссылки
        POST /api/storage/{file.id}/share/ (повторный вызов)
        """
        file = UserFileFactory(user=regular_user, share_token="old_token_123")

        old_token = file.share_token

        url = storage_share_url(file)
        response = auth_client.post(url)

        self.assert_status(response, status.HTTP_200_OK)
        assert response.data["share_token"] != old_token

        file.refresh_from_db()
        assert file.share_token != old_token


@pytest.mark.api
@pytest.mark.django_db
class TestPublicShareAPI(BaseTestAPI):
    """Тесты публичного доступа по ссылкам"""

    def test_download_by_share_link(
        self, api_client, regular_user, storage_public_share_url
    ):
        """
        Тест скачивания файла по публичной ссылке
        GET /api/storage/share/{share_token}/
        """
        file = UserFileFactory(user=regular_user, create_file="shared content")

        # Получаем сгенерированный токен из модели
        share_token = uuid.UUID(file.share_token)

        response = api_client.get(storage_public_share_url(share_token))

        self.assert_status(response, status.HTTP_200_OK)

        content = b"".join(response.streaming_content)
        assert content == b"shared content"
        assert (
            response.headers["Content-Disposition"]
            == f'attachment; filename="{file.original_name}"'
        )

    def test_get_share_info(self, api_client, regular_user, storage_public_share_url):
        """
        Тест получения информации о файле по ссылке
        GET /api/storage/share/{share_token}/?info=true
        """
        file = UserFileFactory(user=regular_user)

        share_token_uuid = uuid.UUID(file.share_token)

        url = storage_public_share_url(str(share_token_uuid))
        response = api_client.get(f"{url}?info=true")

        self.assert_status(response, status.HTTP_200_OK)

        # Проверяем поля, которые реально возвращает сериализатор
        expected_fields = ["share_token", "share_url", "share_token_created"]
        self.assert_response_has_fields(response.data, expected_fields)

        # Проверяем значения
        assert response.data["share_token"] == file.share_token

        # Для URL используем hex (без дефисов)
        expected_url_part = file.share_token  # это уже hex без дефисов
        assert expected_url_part in response.data["share_url"]
        assert (
            response.data["share_url"]
            == f"http://testserver/api/storage/share/{file.share_token}/"
        )

    def test_invalid_share_link(self, api_client, storage_public_share_url):
        """
        Тест недействительной ссылки
        GET /api/storage/share/{invalid_token}/
        """
        invalid_token = uuid.uuid4()

        url = storage_public_share_url(str(invalid_token))
        response = api_client.get(url)

        self.assert_error_response(
            response,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            expected_field="error",
            expected_message="Не удалось загрузить файл",
        )
