import logging
import os
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """Расширенная модель пользователя"""

    full_name = models.CharField("Полное имя", max_length=255)
    email = models.EmailField("Email", unique=True)
    is_admin = models.BooleanField("Администратор", default=False)
    storage_path = models.CharField("Путь к хранилищу", max_length=512, blank=True)

    # Отключаем неиспользуемые поля
    first_name = None
    last_name = None

    class Meta:
        db_table = "accounts_user"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def save(self, *args, **kwargs):
        """Сохранение пользователя и создание директории хранилища"""
        is_new = self.pk is None

        if is_new and not self.storage_path:
            super().save(*args, **kwargs)
            user_dir = f"user_{self.id}_{uuid.uuid4().hex[:8]}"
            self.storage_path = os.path.join("users", user_dir)

            # Сохраняем обновленный путь в БД
            User.objects.filter(pk=self.pk).update(storage_path=self.storage_path)
            self.refresh_from_db()
            self._create_user_storage()
            return

        # Для существующих пользователей
        super().save(*args, **kwargs)

        # Если путь изменился у существующего пользователя
        if not is_new and self.storage_path and not hasattr(self, '_storage_created'):
            pass

    def _create_user_storage(self):
        """Создание директории для хранения файлов пользователя"""
        if not self.storage_path:
            return

        try:
            full_path = os.path.join(settings.MEDIA_ROOT, self.storage_path)
            os.makedirs(full_path, exist_ok=True)
            logger.info(
                f"Создана директория хранилища для пользователя {self.username} (ID: {self.id}): {full_path}"
            )
        except Exception as e:
            logger.error(
                f"Ошибка создания директории для пользователя {self.username}: {str(e)}"
            )

    def get_storage_full_path(self):
        """Получение полного пути к хранилищу пользователя"""

        return os.path.join(settings.MEDIA_ROOT, self.storage_path)

    def __str__(self):
        return self.username
