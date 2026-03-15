import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# URL для доступа к медиа-файлам
MEDIA_URL = "/media/"

# Путь к директории для хранения загруженных файлов
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STORAGE_SETTINGS = {
    "BASE_STORAGE_PATH": MEDIA_ROOT,
    "MAX_FILE_SIZE": 100 * 1024 * 1024,  # 100 MB
    "ALLOWED_EXTENSIONS": [
        ".txt",
        ".pdf",
        ".doc",
        ".docx",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".zip",
        ".rar",
        ".7z",
    ],
    "ALLOWED_MIME_TYPES": [
        "text/plain",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    ],
}

os.makedirs(MEDIA_ROOT, exist_ok=True)

for static_dir in STATICFILES_DIRS:
    os.makedirs(static_dir, exist_ok=True)

os.makedirs(STATIC_ROOT, exist_ok=True)
