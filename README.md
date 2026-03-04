# Настройка переменных окружения
#### Создать файл .env в корне проекта (рядом с manage.py):
```
DJANGO_SECRET_KEY=***
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DJANGO_SUPERUSER_USERNAME=
DJANGO_SUPERUSER_EMAIL=
DJANGO_SUPERUSER_PASSWORD=
```

# Создать каталоги в корне проекта
```
media/
static/
```

# Работа с Poetry
* Установить Poetry
```pip install poetry```
* Установить все зависимости
```poetry install```
* Активировать виртуальное окружение
```poetry shell```
* Показать зависимости
```poetry show```
* Обновить зависимости
```poetry update```
* Создать суперюзера с данными из .env
```poetry run python manage.py createsuperuser --noinput```


# Работа с проектом
* Создать миграции
```python manage.py makemigrations```
* Применить мигранции
```python manage.py migrate```
* Запустить сервер
```python manage.py runserver```
* Создать суперюзера
```python manage.py createsuperuser```
* Создать приложение
```python manage.py startapp accounts ./apps/<name>```


# API Endpoints
* Административный интерфейс
```
POST /api/accounts/users/register/ - регистрация пользователя
POST /api/accounts/users/login/ - вход в систему
POST /api/accounts/users/logout/ - выход из системы
GET /api/accounts/users/me/ - информация о текущем пользователе
GET /api/accounts/users/ - список пользователей
GET PUT PATCH DELETE /api/accounts/users/<id>/ - редактирование пользователя
```
* Работа с файлами
```
GET POST /api/storage/ - список файлов
GET, PUT, PATCH, DELETE /api/storage/{file.id}/" - работа с файлами
GET /api/storage/{file.id}/download/ загрузка файла
GET /api/storage/{file.id}/view/ - просмотр в браузере
POST /api/storage/{file.id}/share/ - создание ссылки
DELETE /api/storage/{file.id}/revoke_share/ - удаляет ссылку
GET /api/storage/share/{share_link}/ - скачивание по ссылке
```

# Линтеры
* Отформатировать код
```poetry run black .```
* Проверить код
```poetry run flake8 .```

# Тестирование
* Запустить тесты
```pytest -n auto```
* Запуск тестов + покрытие кода с полной очисткой старых отчетов
```coverage erase; Remove-Item -Recurse -Force htmlcov -ErrorAction SilentlyContinue; pytest -n auto --cov=. --cov-config=.coveragerc --cov-report=html --cov-report=term-missing```

# Документация апи
[API DOCS](http://127.0.0.1:8000/api/docs/)
