import factory
from django.contrib.auth import get_user_model
from faker import Faker

fake = Faker()
User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Базовый класс для всех фабрик пользователей"""

    class Meta:
        model = User
        abstract = True  # Не создавать экземпляры этого класса
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n:04d}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    full_name = factory.LazyFunction(lambda: fake.name())
    is_active = True

    # Обработка пароля
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "testpass123")

        if create:
            self.save()


class RegularUserFactory(UserFactory):
    """Фабрика для обычных пользователей"""

    class Meta:
        model = User
        skip_postgeneration_save = True

    is_staff = False
    is_superuser = False
    is_admin = False


class AdminUserFactory(UserFactory):
    """Фабрика для администраторов"""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"admin_{n:04d}")
    is_staff = True
    is_superuser = True
    is_admin = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "adminpass123")

        if create:
            self.save()
