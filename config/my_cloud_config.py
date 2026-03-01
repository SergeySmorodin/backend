import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# URL для доступа к медиа-файлам
MEDIA_URL = '/media/'

# Путь к директории для хранения загруженных файлов
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Максимальный размер файла для загрузки (в байтах)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# Разрешенные типы файлов для загрузки
ALLOWED_FILE_TYPES = [
    'image/jpeg', 'image/png', 'application/pdf', 'text/plain',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

ALLOWED_EXTENSIONS = ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.docx', '.xlsx']
