# Генерация ssh ключей для сервера
* Генерация ключей
```ssh-keygen```
* Копирование ключа и добавление в authorized_keys или на сервер через настройки
```cat ~/.ssh/id_rsa.pub```

# Запустить сервер и зайти под учетной записью root
 * Учетная запись root (ввести логин@<ip сервера> и пароль присланный на email)
```ssh root@91.197.99.145```
 * Создать пользователя и пароль
```adduser <username>```
 * Назначить права администратора
```usermod -aG sudo <username>```
 * Выйти из аккаунта root 
```logout```или переключится на нового юзера ```su <username>```
* Войти как новый пользователь, если не использовали переключение
```ssh - <username>@<ip server>```
* Выполнить обновление пакетного менеджера
```sudo apt update```
* Проверить наличие зависимостей гит и пайтон
```git --version``` и ```pyhton3 –-version```
* Установить зависимости (виртуальное окружение, pip и др.)
```sudo apt install python3-venv python3-pip posgresql nginx``` установить в вирт окружении ```gunicorn```
* Проверить статус postgresql 
```sudo systemctl status postgresql```
* Запустить вручную postgres если статус in_active
```sudo systemctl start postgresql```

# Запуск nginx
* Запустить вручную nginx
```sudo systemctl start nginx```
* Проверить статус nginx
```sudo systemctl status nginx```
* Создать конфигурационный файл
```sudo nano /etc/nginx/sites-available/my_cloud_project```
```
server {
    listen 80;
    server_name <ip server>;
    location /static/ {
        root/home/<user_name>/backend/static;
    }
    location = / {
        include proxy_params;
        proxy_pass http://unix:/home/<user_name>/backend/my_cloud_project/project.sock;
        }
    }
```
* Перезагрузить конфигурационный файл
```sudo ln -s /etc/nginx/sites-available/my_cloud_project /etc/nginx/sites-enabled/```
* Перезагрузить nginx
```sudo systemctl reload nginx```
* Проверить статус nginx
```sudo systemctl status nginx```
* Дать полные права ngxinx
```sudo ufw allow 'Nginx Full';```
* Проверить или создать папку static чтобы ngnix мог ее видеть и сам подгружать
```ls``` через виртуальное окружение ```python mange.py collectstatis```

# Работа c gunicorn
* Запуск через gunicorn (отслеживания интерфейса)
```gunicorn my_cloud_project.wsgi-b 0.0.0.0:8000```
* Освободить порт при ошибках
```fuser -k 8000/tcp```
* Создать конфигурационный файл для авто-запуска и перезагрузки сервера
```sudo nano etc/systemd/system/gunicron.service```
```
[Unit]
Description=gunicorn service
After=network.target

[Service]
Group=www-data
User=root
WorkingDirectory=/home/'your username'/backend/
ExecStart=/home/<your_username>/backend/my_cloud_project/bin/gunicorn --access-logfile -\
           --workers=3 \
           --bind unix:/home/<user_name>/backend/my_cloud_project/project.sock shortener.wsgi:application

[Install]
WantedBy=multi-user.target
```
* Запустить сервис
```sudo systemctl start gunicorn```
* * Выключить автосервис
```sudo systemctl enable gunicorn```
* Проверить статус сервиса (должен быть запущенным даже после остановки)
```sudo systemctl status gunicorn```
* Должен появится файл project.sock в папке с настройками приложения (my-cloud-project)


# Загрузка проекта на сервер из git репозитория
* Проверить директорию (должны быть домашняя папка /home/<имя_пользователя>/)
```pwd```
* Проверить содержимое папки
```ls```
* Клонируем проект
```git clone <ссылка на репозиторий>```
* Переходим в директорию проекта
```cd <project_name>```
* Проверить ветку
```git branch``` переход к другой ветке ```git checkout <имя_ветки>```
  
# Установить зависимости с Poetry
* Установить pipx
```sudo apt install -y pipx```
* Установите Poetry
```pipx install poetry```
* Прописать путь в конфигурацию вашего терминала
```pipx ensurepath```
* Применить изменения
```source ~/.bashrc```
* Активировать виртуальное окружение
```poetry shell``` или ```poetry env activate``` или активировать по предложенной команде ```source ...```
* Установить все зависимости
```poetry install```

* Показать зависимости
```poetry show```
* Создать суперюзера с данными из .env
```poetry run python manage.py createsuperuser --noinput```


# Создание БД
* Создать пользователя postgres
```sudo su postgres``` и зайти в панель ```psql```
* Создать пользователя
```CREATE USER <user> WITH SUPERUSER;```
* Установить пароль
```ALTER USER <user> WITH PASSWORD '<password>';```
* Создать базу данных
```CREATE DATABASE <user_name>;```
* Выйти из панели psql
```\q```
* Выйти из пользователя postgres
```exit```

* Зайти в psql под созданным пользователем postgres
```psql```
* Создаем БД для приложения Django
```CREATE DATABASE <db name>;```

# Настройка проекта
* Создать файл .env добавить в него ALLOWED_HOSTS сервера и другие секретные данные
```nano .env```  добавить содержимое, сохранить Ctrl+O, подтвердить enter и выйти по Ctrl+X
* Создать директории
```mkdir media static```
* Создать миграции из активированного окружения
```python manage.py makemigrations```
* Применить миграции
```python manage.py migrate```
* Запустить сервер
```python manage.py runserver 0.0.0.0:8000```



