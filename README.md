# Показать зависимости
poetry show

# Обновить зависимости
poetry update

# Установить все зависимости
poetry install

# Создать миграции
poetry run python manage.py makemigrations

# Применить мигранции
poetry run python manage.py migrate

# Запустить сервер
poetry run python manage.py runserver

# Запустить тесты
poetry run pytest

# Проверка кода
poetry run black .
poetry run flake8 .

# Активировать виртуальное окружение
poetry shell

# Выйти из виртуального окружения
exit

# Создать проект
poetry run django-admin startproject <name> .

# Создать приложение
poetry run python manage.py startapp <name>

# Создать админа
poetry run python manage.py createsuperuser



