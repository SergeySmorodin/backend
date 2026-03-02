import io
import os

import factory
import pytest
from PIL import Image as PILImage
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker

from apps.storage.models import UserFile

fake = Faker()


class UserFileFactory(factory.django.DjangoModelFactory):
    """
    Фабрика для создания тестовых файлов.

    Использование:
        file = UserFileFactory()                          # Текстовый файл
        file = UserFileFactory(create_file=False)         # Только запись в БД
        file = UserFileFactory(create_file="content")     # Строка как содержимое
        file = UserFileFactory(_file_type='image')        # Изображение (через _)
        file = UserFileFactory(original_name='doc.pdf')   # Тип по расширению
    """

    class Meta:
        model = UserFile

    user = factory.SubFactory('your_app.factories.RegularUserFactory')
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

        # === 3. Записываем файл ===
        with open(full_path, 'wb') as f:
            f.write(content)

        # === 4. Обновляем размер в БД ===
        UserFile.objects.filter(pk=self.pk).update(size=len(content))


@pytest.fixture
def test_file_factory():
    """
    Фикстура для создания тестовых файлов для POST запросов

    Примеры:
        text_file = test_file_factory('text', filename='doc.txt', content='Hello')
        image_file = test_file_factory('image', filename='photo.jpg', size=(200, 200))
        pdf_file = test_file_factory('pdf', filename='doc.pdf')
        binary_file = test_file_factory('binary', filename='data.bin', size_kb=5)
    """

    def _make_file(file_type='text', filename=None, **kwargs):
        if filename is None:
            filename = fake.file_name()

        if file_type == 'text':
            content = kwargs.get('content', fake.text())
            if isinstance(content, str):
                content = content.encode('utf-8')
            return SimpleUploadedFile(
                filename,
                content,
                content_type=kwargs.get('content_type', 'text/plain')
            )

        elif file_type == 'image':
            size = kwargs.get('size', (100, 100))
            color = kwargs.get('color', 'red')
            img_format = kwargs.get('format', 'JPEG')

            image = PILImage.new('RGB', size, color=color)
            img_io = io.BytesIO()
            image.save(img_io, format=img_format)

            return SimpleUploadedFile(
                filename,
                img_io.getvalue(),
                content_type=f'image/{img_format.lower()}'
            )

        elif file_type == 'pdf':
            content = kwargs.get('content', b'%PDF-1.4\n%PDF content\n')
            return SimpleUploadedFile(
                filename,
                content,
                content_type='application/pdf'
            )

        elif file_type == 'binary':
            size_kb = kwargs.get('size_kb', 10)
            content = os.urandom(size_kb * 1024)
            return SimpleUploadedFile(
                filename,
                content,
                content_type='application/octet-stream'
            )

        # по расширению
        else:
            ext = os.path.splitext(filename)[1].lower()
            content = kwargs.get('content', fake.text())

            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                file_type = 'image'
            elif ext == '.pdf':
                file_type = 'pdf'
            else:
                file_type = 'text'

            return _make_file(file_type, filename, content=content, **kwargs)

    return _make_file


@pytest.fixture
def text_file(test_file_factory):
    """Фикстура для текстового файла"""
    return test_file_factory('text', filename='test.txt', content='Test content')


@pytest.fixture
def image_file(test_file_factory):
    """Фикстура для изображения"""
    return test_file_factory('image', filename='test.jpg', size=(100, 100))


@pytest.fixture
def pdf_file(test_file_factory):
    """Фикстура для PDF файла"""
    return test_file_factory('pdf', filename='test.pdf')
