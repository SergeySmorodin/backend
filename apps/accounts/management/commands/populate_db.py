from django.core.management.base import BaseCommand
from scripts.populate_db import DatabasePopulator


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить базу перед заполнением (без подтверждения)',
        )
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Создать суперпользователя admin/admin',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=15,
            help='Количество обычных пользователей (по умолчанию: 15)',
        )
        parser.add_argument(
            '--admins',
            type=int,
            default=3,
            help='Количество администраторов (по умолчанию: 3)',
        )
        parser.add_argument(
            '--no-specific',
            action='store_true',
            help='Не создавать специальных пользователей (power_user, shared_user)',
        )
        parser.add_argument(
            '--min-files',
            type=int,
            default=3,
            help='Минимум файлов на пользователя (по умолчанию: 3)',
        )
        parser.add_argument(
            '--max-files',
            type=int,
            default=20,
            help='Максимум файлов на пользователя (по умолчанию: 20)',
        )

    def handle(self, *args, **options):

        populator = DatabasePopulator()

        # Очистка базы
        if options['clear']:
            self.stdout.write(self.style.WARNING('Очистка базы данных...'))

            if not populator.clear_existing_data(confirm=False):
                self.stdout.write(self.style.ERROR('Очистка отменена'))
                return

        # Создание суперпользователя
        if options['create_admin']:
            try:
                populator.create_superuser(username='admin', password='admin')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Не удалось создать суперпользователя: {e}'))

        # Создание обычных пользователей и админов
        users_count = max(0, options['users'])
        admins_count = max(0, options['admins'])

        self.stdout.write(self.style.WARNING(
            f'Создание {users_count} пользователей и {admins_count} админов...'
        ))
        populator.create_users(regular_count=users_count, admin_count=admins_count)

        # Создание специальных пользователей
        if not options['no_specific']:
            populator.create_specific_users()

        # Создание файлов
        min_files = max(1, options['min_files'])
        max_files = max(min_files, options['max_files'])

        populator.create_all_files(files_per_user=(min_files, max_files))

        populator.print_summary()

        self.stdout.write(self.style.SUCCESS('\nБаза данных успешно заполнена'))
        self.stdout.write(self.style.WARNING('Для входа: admin / admin'))
