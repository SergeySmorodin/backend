import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.config.base_test_class.base_test_api_class import BaseTestAPI
from tests.config.data_factories.fake_users_factory import RegularUserFactory

User = get_user_model()


@pytest.mark.api
@pytest.mark.django_db
class TestPermissionUsersDetailAPI(BaseTestAPI):
    """
    Тесты доступа к операциям с конкретным пользователем
    /api/accounts/users/{user.id}/
    """

    @pytest.mark.parametrize(
        "method, expected_status, payload",
        [
            ("get", status.HTTP_403_FORBIDDEN, None),
            ("put", status.HTTP_403_FORBIDDEN, {}),
            ("patch", status.HTTP_403_FORBIDDEN, {}),
            ("delete", status.HTTP_403_FORBIDDEN, None),
        ],
    )
    def test_unauthorized_access(
        self,
        api_client,
        accounts_detail_url,
        regular_user,
        method,
        expected_status,
        payload,
    ):
        """
        Неавторизованный пользователь не имеет доступа к операциям с пользователями
        Параметризованный тест для всех HTTP методов
        /api/accounts/users/{user.id}/
        """
        url = accounts_detail_url(regular_user)

        if method == "get":
            response = api_client.get(url)
        elif method == "put":
            response = api_client.put(url, payload or {}, format="json")
        elif method == "patch":
            response = api_client.patch(url, payload or {}, format="json")
        elif method == "delete":
            response = api_client.delete(url)
        else:
            pytest.fail(f"Неподдерживаемый метод: {method}")

        self.assert_status(response, expected_status)

    def test_admin_has_full_access(
        self, admin_client, accounts_detail_url, regular_user, put_data, patch_data
    ):
        """
        Администратор имеет полный доступ к любому пользователю
        /api/accounts/users/{user.id}/
        """
        # GET
        response = admin_client.get(accounts_detail_url(regular_user))
        assert response.status_code == status.HTTP_200_OK

        # PUT
        response = admin_client.put(
            accounts_detail_url(regular_user),
            put_data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # PATCH
        response = admin_client.patch(
            accounts_detail_url(regular_user),
            patch_data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # DELETE (но не себя)
        another_user = RegularUserFactory()
        response = admin_client.delete(accounts_detail_url(another_user))
        assert response.status_code == status.HTTP_204_NO_CONTENT
