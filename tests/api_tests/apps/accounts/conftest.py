import pytest
from faker import Faker


@pytest.fixture
def test_auth_user_data():
    fake = Faker()

    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "full_name": fake.name(),
    }

    return user_data


@pytest.fixture
def put_data():
    fake = Faker()

    user_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "full_name": fake.name(),
    }

    return user_data


@pytest.fixture
def patch_data():
    fake = Faker()

    user_data = {
        "full_name": fake.name(),
    }

    return user_data


@pytest.fixture
def test_login_data(regular_user):
    user_data = {
        "username": regular_user.username,
        "password": "testpass123"
    }

    return user_data
