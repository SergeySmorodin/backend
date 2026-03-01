import pytest


@pytest.fixture
def storage_url():
    """GET POST"""
    return f'/api/storage/'


@pytest.fixture
def storage_detail_url(storage_url):
    """GET, PUT, PATCH, DELETE /api/storage/{file.id}/"""

    def _url(file):
        return f'{storage_url}{file.id}/'

    return _url


@pytest.fixture
def storage_download_url(storage_url):
    """GET /api/storage/{file.id}/download/"""

    def _url(file):
        return f'{storage_url}{file.id}/download/'

    return _url
