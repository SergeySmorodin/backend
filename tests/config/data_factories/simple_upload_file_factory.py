import io
import os

import pytest
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker

fake = Faker()


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
