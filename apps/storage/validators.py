import logging
import os

from django.conf import settings
from django.core.exceptions import ValidationError

from .models import UserFile

logger = logging.getLogger(__name__)


def validate_file_extension(value):
    """
    Валидация расширения файла
    """
    allowed_extensions = settings.STORAGE_SETTINGS.get("ALLOWED_EXTENSIONS", [])

    if not allowed_extensions:
        return value

    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        allowed_ext_str = ", ".join(allowed_extensions)
        raise ValidationError(
            f"Недопустимое расширение файла: {ext}. "
            f"Разрешенные расширения: {allowed_ext_str}"
        )

    logger.debug(f"Файл {value.name} прошел проверку расширения")
    return value


def validate_file_size(value):
    """
    Валидация размера файла
    """
    max_size = settings.STORAGE_SETTINGS.get(
        "MAX_FILE_SIZE", 100 * 1024 * 1024
    )  # 100 MB по умолчанию

    if value.size > max_size:
        max_size_mb = max_size / 1024 / 1024
        file_size_mb = value.size / 1024 / 1024
        raise ValidationError(
            f"Размер файла ({file_size_mb:.1f} MB) превышает максимально допустимый ({max_size_mb:.0f} MB)"
        )

    logger.debug(f"Файл {value.name} прошел проверку размера ({value.size} bytes)")
    return value


def validate_file_name(value):
    """
    Валидация имени файла
    """
    if not value or not value.name:
        raise ValidationError("Имя файла не может быть пустым")

    if len(value.name) > 255:
        raise ValidationError("Имя файла не должно превышать 255 символов")

    invalid_chars = '<>:"/\\|?*'
    if any(char in value.name for char in invalid_chars):
        raise ValidationError(
            f"Имя файла содержит недопустимые символы. Недопустимо: {invalid_chars}"
        )

    return value


def validate_file_content_type(value):
    """
    Валидация MIME-типа файла
    """
    import magic

    try:
        # Читаем первые 2048 байт для определения типа
        file_start = value.read(2048)
        value.seek(0)  # Возвращаем указатель в начало

        mime = magic.from_buffer(file_start, mime=True)

        allowed_mime_types = settings.STORAGE_SETTINGS.get(
            "ALLOWED_MIME_TYPES",
            [
                "image/jpeg",
                "image/png",
                "image/gif",
                "application/pdf",
                "text/plain",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/zip",
            ],
        )

        if mime not in allowed_mime_types:
            raise ValidationError(f"Недопустимый MIME-тип файла: {mime}")

    except Exception as e:
        logger.warning(f"Не удалось определить MIME-тип файла: {e}")

    return value


def validate_unique_filename(user, filename):
    """
    Генерация уникального имени файла для пользователя
    Возвращает уникальное имя файла
    """

    base, ext = os.path.splitext(filename)

    # Проверяем, существует ли файл с таким именем у пользователя
    if UserFile.objects.filter(user=user, original_name=filename).exists():
        counter = 1
        while UserFile.objects.filter(
            user=user, original_name=f"{base}_{counter:03}{ext}"
        ).exists():
            counter += 1
        new_filename = f"{base}_{counter:03}{ext}"
        logger.info(
            f"Имя файла изменено с {filename} на {new_filename} (конфликт имен)"
        )
        return new_filename

    return filename


class FileValidator:
    """
    Класс-валидатор для комплексной проверки файлов
    Можно использовать в сериализаторах
    """

    def __init__(self, check_extension=True, check_size=True, check_name=True):
        self.check_extension = check_extension
        self.check_size = check_size
        self.check_name = check_name

    def __call__(self, value):
        if self.check_name:
            validate_file_name(value)

        if self.check_extension:
            validate_file_extension(value)

        if self.check_size:
            validate_file_size(value)

        return value
