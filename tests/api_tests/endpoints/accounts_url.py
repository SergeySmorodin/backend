import pytest


@pytest.fixture
def accounts_url():
    return f'/api/accounts/'


@pytest.fixture
def accounts_users_url(accounts_url):
    """GET /api/accounts/users/"""
    return f'{accounts_url}users/'


@pytest.fixture
def accounts_register_url(accounts_users_url):
    """POST /api/accounts/users/register/"""
    return f'{accounts_users_url}register/'


@pytest.fixture
def accounts_login_url(accounts_users_url):
    """POST /api/accounts/users/login/"""
    return f'{accounts_users_url}login/'


@pytest.fixture
def accounts_logout_url(accounts_users_url):
    """POST /api/accounts/users/logout/"""
    return f'{accounts_users_url}logout/'


@pytest.fixture
def accounts_me_url(accounts_users_url):
    """GET /api/accounts/users/me/"""
    return f'{accounts_users_url}me/'


@pytest.fixture
def accounts_detail_url(accounts_users_url):
    """GET, PUT, PATCH, DELETE /api/accounts/users/{user.id}/"""

    def _url(user):
        return f'{accounts_users_url}{user.id}/'

    return _url
