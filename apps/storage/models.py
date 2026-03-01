import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import User
import logging

logger = logging.getLogger(__name__)


def generate_share_token():
    """Генерация уникального токена для доступа к файлу"""
    return uuid.uuid4().hex


class UserFile(models.Model):
    """Модель файла пользователя"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name="Владелец"
    )

    original_name = models.CharField("Оригинальное имя", max_length=255)
    size = models.BigIntegerField("Размер файла", default=0)
    upload_date = models.DateTimeField("Дата загрузки", auto_now_add=True)
    last_download = models.DateTimeField(
        "Последнее скачивание",
        null=True,
        blank=True
    )
    comment = models.TextField("Комментарий", blank=True, default="")
    file_path = models.CharField("Путь к файлу", max_length=512)

    share_token = models.CharField(
        "Токен для доступа",
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    share_token_created = models.DateTimeField(
        "Дата создания токена",
        null=True,
        blank=True
    )

    class Meta:
        db_table = "storage_file"
        verbose_name = "Файл"
        verbose_name_plural = "Файлы"
        ordering = ["-upload_date"]
        indexes = [
            models.Index(fields=['user', '-upload_date']),
            models.Index(fields=['share_token']),
        ]

    def save(self, *args, **kwargs):
        """Автоматическая генерация токена при создании"""
        if not self.share_token and not self.pk:
            self.share_token = generate_share_token()
            self.share_token_created = timezone.now()
        super().save(*args, **kwargs)

    @property
    def full_path(self):
        """Получение полного пути к файлу"""
        return os.path.join(settings.MEDIA_ROOT, self.file_path)

    @property
    def exists(self):
        """Проверка существования файла на диске"""
        return os.path.exists(self.full_path)

    @property
    def size_display(self):
        """Форматирование размера файла для отображения"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def update_download_date(self):
        """Обновление даты последнего скачивания"""
        self.last_download = timezone.now()
        self.save(update_fields=["last_download"])
        logger.debug(f"Обновлена дата скачивания файла {self.id}")

    def regenerate_share_token(self):
        """Генерация нового токена для доступа"""
        self.share_token = generate_share_token()
        self.share_token_created = timezone.now()
        self.save(update_fields=["share_token", "share_token_created"])
        logger.info(f"Сгенерирован новый токен для файла {self.id}")

    def delete(self, *args, **kwargs):
        """Удаление файла с диска при удалении записи из БД"""
        try:
            if self.exists:
                os.remove(self.full_path)
                logger.info(f"Удален физический файл: {self.full_path}")
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {self.full_path}: {e}")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.original_name} ({self.user.username})"
