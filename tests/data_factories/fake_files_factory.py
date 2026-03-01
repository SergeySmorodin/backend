import factory
from django.contrib.auth import get_user_model
from faker import Faker

from tests.data_factories.fake_users_factory import RegularUserFactory

fake = Faker()
User = get_user_model()


class FileFactory(factory.django.DjangoModelFactory):
    """Фабрика для файлов"""

    class Meta:
        model = 'storage.UserFile'

    name = factory.Sequence(lambda n: f'file_{n}.txt')
    owner = factory.SubFactory(RegularUserFactory)
    size = factory.LazyFunction(lambda: fake.random_int(min=1024, max=1048576))
    created_at = factory.LazyFunction(lambda: fake.date_time_this_year())

    @factory.post_generation
    def content(self, create, extracted, **kwargs):
        """Создание тестового файла"""

        if not create:
            return
        from django.core.files.base import ContentFile
        content = extracted or fake.text()
        self.file.save(
            self.name,
            ContentFile(content.encode('utf-8'))
        )
