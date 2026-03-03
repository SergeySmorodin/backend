from dotenv import load_dotenv
import os
from django.core.exceptions import ImproperlyConfigured

# Загрузка переменных из .env файла
load_dotenv()


def get_env_variable(var_name):
    try:
        return os.getenv(var_name)
    except KeyError:
        error_msg = f"Установите переменную окружения {var_name}"
        raise ImproperlyConfigured(error_msg)


# Настройки подключения к базе данных
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
