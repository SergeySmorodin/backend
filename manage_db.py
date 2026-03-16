import psycopg2
from psycopg2 import sql
import argparse
import sys
import os
from dotenv import load_dotenv

"""Скрипт для управления базой данных PostgreSQL: создание, удаление, пересоздание."""

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "dbname": os.getenv("POSTGRES_DB", "my_cloud"),
}

if not DB_CONFIG["password"]:
    print("Ошибка: DB_PASSWORD не задан в .env", file=sys.stderr)
    sys.exit(1)


def connect_to_postgres():
    """Подключается к служебной БД 'postgres'"""
    return psycopg2.connect(
        dbname="postgres",
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
    )


def drop_database(cursor, db_name):
    """Удаляет базу данных, если она существует"""
    cursor.execute(
        sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
    )
    print(f"База данных '{db_name}' успешно удалена")


def create_database(cursor, db_name):
    """Создаёт новую базу данных"""
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    print(f"База данных '{db_name}' успешно создана")


def recreate_database(cursor, db_name):
    """Пересоздаёт базу данных (удалить + создать)"""
    drop_database(cursor, db_name)
    create_database(cursor, db_name)


def main():
    parser = argparse.ArgumentParser(
        description="Управление базой данных PostgreSQL: создание, удаление, пересоздание."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="Создать базу данных")
    group.add_argument("--drop", action="store_true", help="Удалить базу данных")
    group.add_argument(
        "--recreate",
        action="store_true",
        help="Пересоздать базу данных (удалить и создать заново)",
    )

    args = parser.parse_args()
    db_name = DB_CONFIG["dbname"]

    connection = None
    cursor = None

    try:
        connection = connect_to_postgres()
        connection.autocommit = True
        cursor = connection.cursor()

        if args.create:
            create_database(cursor, db_name)
        elif args.drop:
            drop_database(cursor, db_name)
        elif args.recreate:
            recreate_database(cursor, db_name)

    except Exception as e:
        print(f"Произошла ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    main()
