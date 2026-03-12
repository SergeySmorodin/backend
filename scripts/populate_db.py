#!/usr/bin/env python
import os
import sys

import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_cloud_project.settings")
django.setup()

from faker import Faker
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from tests.config.data_factories.fake_files_factory import UserFileFactory
from tests.config.data_factories.fake_users_factory import (
    RegularUserFactory,
    AdminUserFactory,
)

from apps.accounts.models import User
from apps.storage.models import UserFile

User = get_user_model()
fake = Faker("ru_RU")


class DatabasePopulator:
    """Класс для заполнения базы данных тестовыми данными"""

    def __init__(self):
        self.users = []
        self.files = []
        self.stats = {
            "users_created": 0,
            "admins_created": 0,
            "files_created": 0,
            "shared_files": 0,
        }

    def clear_existing_data(self, confirm=True):
        """Очистка существующих данных"""

        if confirm:
            response = input("Удалить существующие файлы и пользователей? (y/N): ")
            if response.lower() != "y":
                print("Операция отменена")
                return False

        file_count = UserFile.objects.count()
        for file in UserFile.objects.all():
            try:
                file.delete()
            except Exception as e:
                print(f"Ошибка при удалении файла {file.id}: {e}")

        User.objects.all().delete()

        return True

    def create_superuser(
            self, username="admin", password="admin", email="admin@example.com"
    ):
        """Создание суперпользователя с известными данными"""

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            print(f"Суперпользователь {username} уже существует")
            return None

        try:
            superuser = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                full_name="Администратор Системы",
                is_admin=True,
                is_active=True,
            )
            self.users.append(superuser)
            self.stats["admins_created"] += 1
            return superuser
        except Exception as e:
            print(f"Ошибка создания суперпользователя: {e}")
            return None, {"Ошибка создания супера"}

    def create_users(self, regular_count=10, admin_count=2):
        """Создание тестовых пользователей"""

        for i in range(admin_count):
            try:
                user = AdminUserFactory(
                    username=fake.user_name() + f"_{i}",
                    email=fake.email(),
                    full_name=fake.name(),
                    is_admin=True,
                )
                self.users.append(user)
                self.stats["admins_created"] += 1
                print(f"Админ создан: {user.username} ({user.full_name})")
            except Exception as e:
                print(f"`Ошибка создания админа: {e}")

        for i in range(regular_count):
            try:
                user = RegularUserFactory(
                    username=fake.user_name() + f"_{i + admin_count}",
                    email=fake.email(),
                    full_name=fake.name(),
                    is_admin=False,
                )
                self.users.append(user)
                self.stats["users_created"] += 1
                print(f"Пользователь создан: {user.username} ({user.full_name})")
            except Exception as e:
                print(f"Ошибка создания пользователя: {e}")

        return self.users

    def create_files_for_user(self, user, min_files=1, max_files=15):
        """Создание файлов для конкретного пользователя"""

        file_count = random.randint(min_files, max_files)
        created_files = []

        file_types = ["text", "image", "pdf", "archive"]
        file_extensions = {
            "text": [".txt", ".doc", ".docx", ".md"],
            "image": [".jpg", ".jpeg", ".png", ".gif"],
            "pdf": [".pdf"],
            "archive": [".zip", ".rar", ".7z"],
        }

        for _ in range(file_count):
            try:
                file_type = random.choice(file_types)
                ext = random.choice(file_extensions[file_type])

                file_name = fake.file_name(extension=ext[1:])

                file = UserFileFactory(
                    user=user,
                    original_name=file_name,
                    comment=fake.sentence() if random.random() > 0.3 else "",
                )

                # Случайно расшариваем файлы (30%)
                if random.random() < 0.3:
                    file.regenerate_share_token()
                    self.stats["shared_files"] += 1

                # Обновляем дату последнего скачивания для некоторых файлов
                if random.random() < 0.4:
                    days_ago = random.randint(1, 30)
                    file.last_download = timezone.now() - timedelta(days=days_ago)
                    file.save(update_fields=["last_download"])

                created_files.append(file)
                self.stats["files_created"] += 1

            except Exception as e:
                print(f"Ошибка создания файла для {user.username}: {e}")

        return created_files

    def create_all_files(self, files_per_user=(1, 15), shared_ratio=0.3):
        """Создание файлов для всех пользователей"""

        for user in self.users:
            if user.is_superuser:
                continue

            min_files, max_files = files_per_user
            file_count = random.randint(min_files, max_files)

            self.create_files_for_user(user, file_count, file_count)

    def create_specific_users(self):
        """Создание специальных пользователей для тестирования"""

        # Пользователь с большим количеством файлов
        power_user = RegularUserFactory(
            username="power_user",
            email="power@example.com",
            full_name="Мощный Пользователь",
            is_admin=False,
        )
        self.users.append(power_user)
        self.stats["users_created"] += 1

        for i in range(50):
            try:
                UserFileFactory(
                    user=power_user,
                    original_name=f"file_{i:03d}_{fake.file_name()}",
                    comment=fake.sentence(),
                )
                self.stats["files_created"] += 1
            except Exception as e:
                print(f"Ошибка создания файла {i}: {e}")

        # Пользователь с расшаренными файлами
        shared_user = RegularUserFactory(
            username="shared_user",
            email="shared@example.com",
            full_name="Общий Пользователь",
            is_admin=False,
        )
        self.users.append(shared_user)
        self.stats["users_created"] += 1

        for i in range(10):
            file = UserFileFactory(
                user=shared_user,
                original_name=f"shared_{i}_{fake.file_name()}",
                comment=fake.sentence(),
            )
            file.regenerate_share_token()
            self.stats["shared_files"] += 1
            self.stats["files_created"] += 1

    def print_summary(self):
        """Вывод статистики"""

        if self.users:
            for user in self.users:
                file_count = UserFile.objects.filter(user=user).count()
                shared_count = UserFile.objects.filter(
                    user=user, share_token__isnull=False
                ).count()
                print(
                    f"  • {user.username}: {file_count} файлов ({shared_count} расшарено)"
                )

        print("\n🔐 ИНФОРМАЦИЯ ДЛЯ ВХОДА:")
        print("  • Обычные пользователи: пароль 'testpass123'")
        print("  • Администраторы: пароль 'adminpass123'")
        print("  • Power user: power_user / testpass123")
        print("  • Shared user: shared_user / testpass123")


def run():
    """Основная функция для запуска скрипта"""

    populator = DatabasePopulator()

    if not populator.clear_existing_data(confirm=True):
        return

    populator.create_superuser(username="admin", password="admin")
    populator.create_users(regular_count=15, admin_count=3)
    populator.create_specific_users()
    populator.create_all_files(files_per_user=(3, 20), shared_ratio=0.3)
    populator.print_summary()


if __name__ == "__main__":
    run()
