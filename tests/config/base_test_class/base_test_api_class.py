from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


class BaseTestAPI:
    """
    Базовый класс для всех API тестов

    Предоставляет универсальные методы для проверки API ответов,
    работы с пользователями и обработки ошибок
    """

    # ================== Базовые проверки ==================

    def assert_status(self, response, expected_status, message=None):
        """Проверка статус-кода ответа"""

        if isinstance(expected_status, (list, tuple)):
            assert response.status_code in expected_status, message or (
                f"Ожидался один из статусов {expected_status}, "
                f"получен {response.status_code}. "
                f"Ответ: {response.content.decode('utf-8')}"
            )
        else:
            assert response.status_code == expected_status, message or (
                f"Ожидался статус {expected_status}, "
                f"получен {response.status_code}. "
                f"Ответ: {response.content.decode('utf-8')}"
            )

    def assert_response_has_fields(self, response_data, expected_fields):
        """
        Проверка наличия обязательных полей в ответе

        Args:
            response_data: Данные ответа (dict)
            expected_fields: Список ожидаемых полей
        """
        for field in expected_fields:
            assert (
                field in response_data
            ), f"Поле '{field}' отсутствует в ответе. Доступные поля: {list(response_data.keys())}"

    def assert_response_equals(self, response, expected_data, ignore_fields=None):
        """
        Проверка полного соответствия данных ответа

        Args:
            response: HTTP ответ
            expected_data: Ожидаемые данные
            ignore_fields: Поля для игнорирования при сравнении
        """
        response_data = response.data if hasattr(response, "data") else response

        if ignore_fields:
            response_data = {
                k: v for k, v in response_data.items() if k not in ignore_fields
            }
            expected_data = {
                k: v for k, v in expected_data.items() if k not in ignore_fields
            }

        assert (
            response_data == expected_data
        ), f"Данные не совпадают.\nОжидалось: {expected_data}\nПолучено: {response_data}"

    # ================== Проверки пользователей ==================

    def assert_user_data(self, response_data, user, fields_to_check=None):
        """
        Проверка соответствия данных пользователя

        Args:
            response_data: Данные ответа
            user: Объект пользователя для сравнения
            fields_to_check: Список полей для проверки (по умолчанию: id, username, email)
        """
        if fields_to_check is None:
            fields_to_check = ["id", "username", "email"]

        if hasattr(user, "refresh_from_db"):
            user.refresh_from_db()

        for field in fields_to_check:
            if field in response_data and hasattr(user, field):
                expected_value = getattr(user, field)
                actual_value = response_data[field]
                assert (
                    actual_value == expected_value
                ), f"Поле '{field}': ожидалось '{expected_value}', получено '{actual_value}'"

    def assert_user_created(self, response, expected_data):
        """
        Проверка успешного создания пользователя

        Args:
            response: HTTP ответ
            expected_data: Ожидаемые данные пользователя
        """
        self.assert_status(response, status.HTTP_201_CREATED)
        self.assert_response_has_fields(response.data, ["id", "username", "email"])
        self.assert_user_data(response.data, expected_data)

    # ================== Проверки прав доступа ==================

    def assert_permission_denied(
        self,
        response,
        expected_status=status.HTTP_403_FORBIDDEN,
        check_error_message=False,
    ):
        """
        Проверка отказа в доступе

        Args:
            response: HTTP ответ
            expected_status: Ожидаемый статус-код ошибки
            check_error_message: Проверять ли наличие сообщения об ошибке
        """
        self.assert_status(response, expected_status)

        if check_error_message and response.data:
            error_text = self._extract_error_text(response.data)
            assert any(
                word in error_text.lower()
                for word in ["доступ", "прав", "permission", "denied"]
            ), f"Ответ не содержит сообщение об отказе в доступе: {error_text}"

    def assert_unauthorized(self, response):
        """
        Проверка неавторизованного доступа (401)

        Args:
            response: HTTP ответ
        """
        self.assert_status(response, status.HTTP_401_UNAUTHORIZED)

    # ================== Проверки операций CRUD ==================

    def assert_get_success(self, response, expected_data=None):
        """
        Проверка успешного GET запроса

        Args:
            response: HTTP ответ
            expected_data: Ожидаемые данные (опционально)
        """
        self.assert_status(response, status.HTTP_200_OK)
        if expected_data is not None:
            assert (
                response.data == expected_data
            ), f"Полученные данные не совпадают с ожидаемыми"

    def assert_create_success(self, response, expected_data=None):
        """
        Проверка успешного создания (POST)

        Args:
            response: HTTP ответ
            expected_data: Ожидаемые данные (опционально)
        """
        self.assert_status(response, status.HTTP_201_CREATED)
        if expected_data:
            self.assert_response_equals(response, expected_data)

    def assert_update_success(
        self, response, updated_data, obj, fields_to_check=None, expected_status=None
    ):
        """
        Проверка успешного обновления (PUT/PATCH)

        Args:
            response: HTTP ответ
            updated_data: Отправленные данные для обновления
            obj: Объект для проверки обновления
            fields_to_check: Список полей для проверки
            expected_status: Ожидаемый статус-код (по умолчанию [200, 201])
        """
        if expected_status is None:
            expected_status = [status.HTTP_200_OK, status.HTTP_201_CREATED]

        self.assert_status(response, expected_status)

        if hasattr(obj, "refresh_from_db"):
            obj.refresh_from_db()

        if fields_to_check is None:
            fields_to_check = updated_data.keys()

        for field in fields_to_check:
            if field in updated_data:
                expected_value = updated_data[field]
                actual_value = getattr(obj, field)
                assert (
                    actual_value == expected_value
                ), f"Поле '{field}': ожидалось '{expected_value}', получено '{actual_value}'"

    def assert_delete_success(self, response, obj_id, model=None):
        """
        Проверка успешного удаления (DELETE)

        Args:
            response: HTTP ответ
            obj_id: ID удаленного объекта
            model: Модель для проверки существования объекта
        """
        self.assert_status(response, status.HTTP_204_NO_CONTENT)

        if model:
            assert not model.objects.filter(
                id=obj_id
            ).exists(), f"Объект с id {obj_id} все еще существует в БД"

    # ================== Проверки ошибок ==================

    def assert_error_response(
        self, response, expected_status, expected_field=None, expected_message=None
    ):
        """
        Универсальная проверка ответа с ошибкой

        Args:
            response: HTTP ответ
            expected_status: Ожидаемый статус-код ошибки
            expected_field: Ожидаемое поле с ошибкой
            expected_message: Ожидаемое сообщение об ошибке
        """
        self.assert_status(response, expected_status)

        if expected_field and response.data:
            if isinstance(response.data, dict):
                assert (
                    expected_field in response.data
                ), f"Поле '{expected_field}' отсутствует в ответе. Доступные поля: {list(response.data.keys())}"

        if expected_message and response.data:
            error_text = self._extract_error_text(response.data)
            assert (
                expected_message.lower() in error_text.lower()
            ), f"Сообщение '{expected_message}' не найдено в ответе: {error_text}"

    def assert_validation_error(self, response, field=None):
        """
        Проверка ошибки валидации (400)

        Args:
            response: HTTP ответ
            field: Поле с ошибкой валидации
        """
        self.assert_error_response(
            response, status.HTTP_400_BAD_REQUEST, expected_field=field
        )

    def assert_not_found(self, response):
        """
        Проверка ошибки 404 Not Found

        Args:
            response: HTTP ответ
        """
        self.assert_status(response, status.HTTP_404_NOT_FOUND)

    # ================== Вспомогательные методы ==================

    def _extract_error_text(self, data):
        """
        Извлечение текста ошибки из различных форматов ответа DRF

        Args:
            data: Данные ответа

        Returns:
            str: Объединенный текст ошибок
        """
        error_messages = []

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    error_messages.append(value)
                elif isinstance(value, list):
                    error_messages.extend([str(v) for v in value])
                elif isinstance(value, dict):
                    error_messages.append(self._extract_error_text(value))
        elif isinstance(data, (str, bytes)):
            error_messages.append(str(data))
        elif isinstance(data, list):
            for item in data:
                error_messages.append(str(item))

        return " ".join(filter(None, error_messages))
