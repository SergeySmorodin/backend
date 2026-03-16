# Инструкция по развертыванию проекта локально

### Клонировать репозиторий бэкенда
```git clone https://github.com/SergeySmorodin/backend.git```
### Клонировать репозиторий фронтенда
```git clone https://github.com/SergeySmorodin/frontend.git```


# *РАЗВЕРТЫВАНИЕ БЭКЕНДА*
## 1. Настройка переменных окружения
* В директории backend создать файл .env в корне проекта (рядом с manage.py):
* Сгенерировать SECRET_KEY
```python -c "from secrets import token_urlsafe; print(token_urlsafe(50))"```
* Заполнить файл .env по примеру ниже, сразу заполнить значения для Postgres переменных
```
DJANGO_SECRET_KEY=***
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173
```
* Выполнить команду в терминале или из README.md для создания пустой БД с параметрами из .env
```python manage_db.py --create``` доступные флаги ```--drop и --recreate```

## 2. Активация виртуального окружения и установка зависимостей
* Установить Poetry
```pip install poetry```
* Активировать виртуальное окружение из папки backend
```poetry env activate```
* Проверить установленные библиотеки
```poetry show```
* При отсутствии установить зависимости
```poetry install --no-root```
* При ошибках удалить lock file и повторно выполнить команду установки
```rm poetry.lock``` и переустановить ```poetry install --no-root```

## 3. Создание локальной базы данных
* Создать миграции
```python manage.py makemigrations```
* Применить миграции
```python manage.py migrate```

## 4. Заполнение базы тестовыми пользователями
* Создать администратора admin/admin и обычных юзеров
```python manage.py populate_db --clear --create-admin```

## 5. Запуск сервера
```python manage.py runserver```


# *РАЗВЕРТЫВАНИЕ ФРОНТЕНДА*
## 1. Настройка переменных окружения
#### В директории frontend/my-app создать файл .env в корне проекта (рядом с package.json):
```VITE_API_URL=http://localhost:8000```

## 2. Установка зависимостей
* Перейти в папку проекта
```cd my-app```
* Установить пакеты npm и зависимости
```npm install```
* Запустить проект в режиме разработки
```npm run dev```
* Открыть сайт в браузере по адресу http://localhost:5173/


# *ДОКУМЕНТАЦИЯ АПИ*
[API DOCS](http://127.0.0.1:8000/api/docs/)

# API Endpoints
### Административный интерфейс
```
POST /api/accounts/users/register/ - регистрация пользователя
POST /api/accounts/users/login/ - вход в систему
POST /api/accounts/users/logout/ - выход из системы
GET /api/accounts/users/me/ - информация о текущем пользователе
GET /api/accounts/users/ - список пользователей
GET PUT PATCH DELETE /api/accounts/users/<id>/ - редактирование пользователя
```
### Работа с файлами
```
GET POST /api/storage/ - список файлов
GET, PUT, PATCH, DELETE /api/storage/{file.id}/" - работа с файлами
GET /api/storage/{file.id}/download/ загрузка файла
GET /api/storage/{file.id}/view/ - просмотр в браузере
POST /api/storage/{file.id}/share/ - создание ссылки
DELETE /api/storage/{file.id}/revoke_share/ - удаляет ссылку
GET /api/storage/share/{share_token}/ - скачивание по ссылке
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
