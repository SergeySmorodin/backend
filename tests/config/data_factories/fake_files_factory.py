import io
import os

import factory
from PIL import Image as PILImage
from django.conf import settings
from faker import Faker

from apps.storage.models import UserFile

fake = Faker()


class UserFileFactory(factory.django.DjangoModelFactory):
    """
    Фабрика для создания тестовых файлов

    Использование:
        file = UserFileFactory()                          # Текстовый файл
        file = UserFileFactory(create_file=False)         # Только запись в БД
        file = UserFileFactory(create_file="content")     # Строка как содержимое
        file = UserFileFactory(_file_type='image')        # Изображение (через _)
        file = UserFileFactory(original_name='doc.pdf')   # Тип по расширению
    """

    class Meta:
        model = UserFile
        skip_postgeneration_save = True  # отключение авто сохранения

    user = factory.SubFactory('tests.config.data_factories.fake_users_factory.RegularUserFactory')
    original_name = factory.LazyAttribute(lambda _: fake.file_name())
    comment = factory.LazyAttribute(lambda _: fake.sentence())

    file_path = factory.LazyAttribute(
        lambda o: os.path.join(o.user.storage_path, o.original_name)
    )

    size = factory.LazyAttribute(lambda _: fake.random_int(min=1024, max=10 * 1024 * 1024))

    @factory.post_generation
    def create_file(self, create, extracted, **kwargs):
        """
        Создаёт физический файл на диске.
        file_type передаётся через kwargs (например, _file_type='image')
        """
        if not create or extracted is False:
            return

        full_path = os.path.join(settings.MEDIA_ROOT, self.file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        content = None
        file_ext = os.path.splitext(self.original_name)[1].lower()

        force_type = kwargs.get('_file_type', kwargs.get('file_type'))

        if isinstance(extracted, bytes):
            content = extracted
        elif isinstance(extracted, str):
            content = extracted.encode('utf-8')
        elif isinstance(extracted, dict):
            raw_content = extracted.get('content')
            if isinstance(raw_content, str):
                content = raw_content.encode('utf-8')
            elif isinstance(raw_content, bytes):
                content = raw_content

        # генерируем по типу
        if content is None:
            target_type = force_type
            if not target_type:
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    target_type = 'image'
                elif file_ext == '.pdf':
                    target_type = 'pdf'
                else:
                    target_type = 'text'

            if target_type == 'image':
                img = PILImage.new('RGB', (100, 100), color='red')
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG')
                content = buffer.getvalue()
            elif target_type == 'pdf':
                content = b"%PDF-1.4\n%Fake PDF Content\n"
            else:
                content = fake.text().encode('utf-8')

        # Записываем файл
        with open(full_path, 'wb') as f:
            f.write(content)

        # Обновляем размер в БД и сохраняем объект
        UserFile.objects.filter(pk=self.pk).update(size=len(content))

        # Сохраняем объект после создания файла
        if create:
            self.save()
