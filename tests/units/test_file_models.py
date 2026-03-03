import os
from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from apps.storage.models import UserFile, generate_share_token
from tests.config.data_factories.fake_users_factory import RegularUserFactory

User = get_user_model()


@pytest.mark.units
@pytest.mark.django_db
class TestUserFileModel:
    """Тесты для модели UserFile"""

    def test_create_file(self, regular_user):
        """Тест создания файла в БД"""
        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        assert file.id is not None
        assert file.user == regular_user
        assert file.original_name == "test.txt"
        assert file.size == 1024
        assert file.file_path == "user_files/test.txt"
        assert file.upload_date is not None
        assert file.comment == ""
        assert file.share_token is not None
        assert file.share_token_created is not None
        assert file.last_download is None

    def test_auto_generate_share_token(self, regular_user):
        """Тест автоматической генерации токена при создании"""

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        assert file.share_token is not None
        assert len(file.share_token) == 32
        assert file.share_token_created is not None

    def test_dont_generate_token_if_exists(self, regular_user):
        """Тест: токен не генерируется, если уже задан"""

        custom_token = "custom_token_123"
        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
            share_token=custom_token,
            share_token_created=timezone.now(),
        )

        assert file.share_token == custom_token
        assert len(file.share_token) != 32

    def test_unique_share_token(self, regular_user):
        """Тест уникальности токена"""

        file1 = UserFile.objects.create(
            user=regular_user,
            original_name="test1.txt",
            size=1024,
            file_path="user_files/test1.txt",
        )

        token = file1.share_token

        # Пытаемся создать файл с таким же токеном
        with pytest.raises(IntegrityError):
            UserFile.objects.create(
                user=regular_user,
                original_name="test2.txt",
                size=1024,
                file_path="user_files/test2.txt",
                share_token=token,
            )

    def test_full_path_property(self, regular_user):
        """Тест свойства full_path"""

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        expected_path = os.path.join(settings.MEDIA_ROOT, "user_files/test.txt")
        assert file.full_path == expected_path

    def test_exists_property_file_exists(self, regular_user, temp_media_root):
        """Тест exists для существующего файла"""

        file_path = os.path.join(temp_media_root, "user_files", "test.txt")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write("test content")

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        assert file.exists is True

    def test_exists_property_file_not_exists(self, regular_user):
        """Тест exists для несуществующего файла"""

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/nonexistent.txt",
        )

        assert file.exists is False

    def test_size_display_property(self, regular_user):
        """Тест форматирования размера файла"""

        test_cases = [
            (500, "500.0 B"),
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (1048576, "1.0 MB"),
            (1572864, "1.5 MB"),
            (1073741824, "1.0 GB"),
        ]

        for size, expected in test_cases:
            file = UserFile.objects.create(
                user=regular_user,
                original_name="test.txt",
                size=size,
                file_path=f"user_files/test_{size}.txt",
            )
            assert file.size_display == expected

    def test_update_download_date(self, regular_user):
        """Тест обновления даты последнего скачивания"""

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        assert file.last_download is None

        # Сохраняем время до обновления
        before_update = timezone.now()

        # Обновляем дату
        file.update_download_date()
        file.refresh_from_db()

        assert file.last_download is not None
        assert file.last_download >= before_update

    def test_regenerate_share_token(self, regular_user):
        """Тест генерации нового токена"""

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        old_token = file.share_token
        old_token_created = file.share_token_created

        # Ждем немного, чтобы время отличалось
        import time

        time.sleep(0.01)

        # Генерируем новый токен
        file.regenerate_share_token()

        assert file.share_token != old_token
        assert file.share_token_created > old_token_created
        assert len(file.share_token) == 32

    def test_str_method(self, regular_user):
        """Тест строкового представления"""

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        expected = f"test.txt ({regular_user.username})"
        assert str(file) == expected

    def test_file_ordering(self, regular_user):
        """Тест сортировки по дате загрузки (новые сверху)"""

        # Создаем файлы с разными датами
        file1 = UserFile.objects.create(
            user=regular_user,
            original_name="old.txt",
            size=1024,
            file_path="user_files/old.txt",
        )
        file1.upload_date = timezone.now() - timedelta(days=2)
        file1.save()

        file2 = UserFile.objects.create(
            user=regular_user,
            original_name="new.txt",
            size=1024,
            file_path="user_files/new.txt",
        )
        file2.upload_date = timezone.now() - timedelta(days=1)
        file2.save()

        file3 = UserFile.objects.create(
            user=regular_user,
            original_name="newest.txt",
            size=1024,
            file_path="user_files/newest.txt",
        )
        file3.upload_date = timezone.now()
        file3.save()

        files = UserFile.objects.filter(user=regular_user)
        assert files[0].original_name == "newest.txt"
        assert files[1].original_name == "new.txt"
        assert files[2].original_name == "old.txt"

    def test_cascade_delete(self, regular_user):
        """Тест каскадного удаления при удалении пользователя"""

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        user_id = regular_user.id
        file_id = file.id

        regular_user.delete()

        assert not UserFile.objects.filter(id=file_id).exists()
        assert not User.objects.filter(id=user_id).exists()


@pytest.mark.units
@pytest.mark.django_db
class TestUserFilePhysicalDeletion:
    """Тесты для физического удаления файлов"""

    def test_delete_file_physical(self, regular_user, temp_media_root):
        """Тест удаления физического файла при удалении записи"""

        file_path = os.path.join(temp_media_root, "user_files", "test.txt")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write("test content")

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/test.txt",
        )

        assert os.path.exists(file_path)

        file.delete()

        # Проверяем, что файл удален с диска
        assert not os.path.exists(file_path)

    def test_delete_file_record_without_physical(self, regular_user):
        """Тест удаления записи без физического файла"""

        file = UserFile.objects.create(
            user=regular_user,
            original_name="test.txt",
            size=1024,
            file_path="user_files/nonexistent.txt",
        )

        try:
            file.delete()
        except Exception as e:
            pytest.fail(f"Удаление вызвало ошибку: {e}")

    def test_bulk_delete_doesnt_remove_physical(self, regular_user, temp_media_root):
        """Тест: массовое удаление через queryset не удаляет физические файлы"""

        files = []
        for i in range(3):
            file_path = os.path.join(temp_media_root, "user_files", f"test{i}.txt")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(f"test content {i}")

            file = UserFile.objects.create(
                user=regular_user,
                original_name=f"test{i}.txt",
                size=1024,
                file_path=f"user_files/test{i}.txt",
            )
            files.append(file)

        # Удаляем через queryset
        UserFile.objects.filter(user=regular_user).delete()

        # Проверяем, что файлы остались на диске
        for i in range(3):
            file_path = os.path.join(temp_media_root, "user_files", f"test{i}.txt")
            assert os.path.exists(file_path), f"Файл {file_path} должен существовать"

    def test_multiple_files_different_users(self, regular_user):
        """Тест работы с файлами разных пользователей"""

        another_user = RegularUserFactory()
        # Создаем файлы для первого пользователя
        file1 = UserFile.objects.create(
            user=regular_user,
            original_name="user1_file.txt",
            size=1024,
            file_path="user1/test.txt",
        )

        # Создаем файлы для второго пользователя
        file2 = UserFile.objects.create(
            user=another_user,
            original_name="user2_file.txt",
            size=2048,
            file_path="user2/test.txt",
        )

        assert file1.user == regular_user
        assert file2.user == another_user

        assert UserFile.objects.filter(user=regular_user).count() == 1
        assert UserFile.objects.filter(user=another_user).count() == 1


@pytest.mark.django_db
class TestGenerateShareToken:
    """Тесты для функции generate_share_token"""

    def test_generate_token_string(self):
        """Тест генерации токена"""

        token = generate_share_token()
        assert isinstance(token, str)
        assert len(token) == 32
        assert all(c in "0123456789abcdef" for c in token)

    def test_generate_unique_tokens(self):
        """Тест уникальности токенов"""

        tokens = set()
        for _ in range(100):
            token = generate_share_token()
            assert token not in tokens
            tokens.add(token)

        assert len(tokens) == 100
