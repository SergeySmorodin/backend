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

