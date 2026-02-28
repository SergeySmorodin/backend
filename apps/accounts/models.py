import os
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import logging

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
        """Создание директории пользователя при сохранении"""

        if not self.storage_path:
            # Уникальный путь для хранилища
            user_dir = f"user_{self.id}_{uuid.uuid4().hex[:8]}"
            self.storage_path = os.path.join("users", user_dir)

        super().save(*args, **kwargs)

        if not self.is_superuser:
            self._create_user_storage()

    def _create_user_storage(self):
        """Создание директории для хранения файлов пользователя"""

        try:
            full_path = os.path.join(settings.MEDIA_ROOT, self.storage_path)
            os.makedirs(full_path, exist_ok=True)
            logger.info(
                f"Создана директория хранилища для пользователя {self.username}: {full_path}"
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
