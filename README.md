# Настройка переменных окружения
Создайте файл .env в корне проекта (рядом с manage.py):

DJANGO_SECRET_KEY=***
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=***
POSTGRES_USER=***
POSTGRES_PASSWORD=***
POSTGRES_HOST=localhost
POSTGRES_PORT=5432




# Активировать виртуальное окружение
poetry shell

# Выйти из виртуального окружения
exit

# Установить все зависимости
poetry install

# Показать зависимости
poetry show

# Обновить зависимости
poetry update

# Создать миграции
python manage.py makemigrations

# Применить мигранции
python manage.py migrate

# Запустить сервер
python manage.py runserver

# Запустить тесты
pytest

# Проверка кода
poetry run black .
poetry run flake8 .





# Создать проект
django-admin startproject <name> .

# Создать приложение
python manage.py startapp accounts ./apps/accounts
python manage.py startapp storage ./apps/storage


# Создать суперюзера
python manage.py createsuperuser


# API Endpoints
```
Административный интерфейс:
POST /api/accounts/users/register/ - регистрация пользователя

POST /api/accounts/users/login/ - вход в систему

POST /api/accounts/users/logout/ - выход из системы

GET /api/accounts/users/me/ - информация о текущем пользователе

GET /api/accounts/users/ - список пользователей

GET PUT PATCH DELETE /api/accounts/users/<id>/ - редактирование пользователя

```
