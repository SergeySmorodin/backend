import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGE_SETTINGS = {
    "BASE_STORAGE_PATH": str(MEDIA_ROOT),
    "MAX_FILE_SIZE": 100 * 1024 * 1024,  # 100 MB
    "ALLOWED_EXTENSIONS": [
        ".txt", ".pdf", ".doc", ".docx",
        ".jpg", ".jpeg", ".png", ".gif",
        ".zip", ".rar", ".7z",
        ".xlsx", ".xls",
    ],
    "ALLOWED_MIME_TYPES": [
        "text/plain",
        "application/pdf",
        "image/jpeg", "image/png", "image/gif",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ],
}

os.makedirs(MEDIA_ROOT, exist_ok=True)

for static_dir in STATICFILES_DIRS:
    os.makedirs(static_dir, exist_ok=True)

os.makedirs(STATIC_ROOT, exist_ok=True)
