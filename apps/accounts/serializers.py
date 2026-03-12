import logging

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """Основной сериализатор пользователя"""

    full_name = serializers.CharField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    storage_path = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "is_admin",
            "date_joined",
            "last_login",
            "storage_path",
        ]
        read_only_fields = fields


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя (регистрация)"""

    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Пользователь с таким email уже существует",
            )
        ],
    )

    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Пользователь с таким username уже существует",
            )
        ],
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2", "full_name"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        logger.info(f"Создан новый пользователь: {user.username} (ID: {user.id})")
        return user


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор для входа пользователя"""

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, style={"input_type": "password"}, write_only=True
    )

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                logger.warning(f"Неудачная попытка входа для пользователя: {username}")
                raise serializers.ValidationError(
                    "Неверное имя пользователя или пароль"
                )
            logger.info(f"Успешный вход пользователя: {user.username}")
            if not user.is_active:
                raise serializers.ValidationError("Пользователь деактивирован")
        else:
            raise serializers.ValidationError(
                "Необходимо указать имя пользователя и пароль"
            )

        attrs["user"] = user
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка пользователей (в админке)"""

    is_admin = serializers.BooleanField(read_only=True)

    # Статистика хранилища
    storage_info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "is_admin",
            "is_active",
            "date_joined",
            "last_login",
            "storage_info",
        ]
        read_only_fields = fields

    def get_storage_info(self, obj):
        """Возвращаем статистику для админов"""
        if hasattr(obj, "files_count"):
            return {
                "file_count": obj.files_count or 0,
                "total_size": obj.total_size or 0,
            }
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления пользователя (PUT/PATCH)"""

    is_admin = serializers.BooleanField(required=False)
    password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )
    password2 = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ["username", "email", "full_name", "is_admin", "password", "password2"]
        extra_kwargs = {
            "username": {"required": False, "allow_blank": False},
            "email": {"required": False, "allow_blank": False},
            "full_name": {"required": False, "allow_blank": False},
        }

    def validate(self, attrs):
        """Проверка совпадения паролей"""
        password = attrs.get("password")
        password2 = attrs.get("password2")

        if password or password2:
            if password != password2:
                raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def validate_email(self, value):
        """Валидация уникальности email при обновлении"""
        user = self.instance
        if user and value == user.email:
            return value
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует"
            )
        return value

    def validate_username(self, value):
        """Валидация уникальности username при обновлении"""
        user = self.instance
        if user and value == user.username:
            return value
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует"
            )
        return value

    def validate_is_admin(self, value):
        """Только админы могут менять is_admin"""
        request = self.context.get("request")

        # Если поле не меняется - пропускаем
        if self.instance and self.instance.is_admin == value:
            return value

        if request and not (
            request.user.is_staff or request.user.is_admin or request.user.is_superuser
        ):
            if self.instance and self.instance.is_admin != value:
                raise serializers.ValidationError(
                    "Только администратор может изменять права администратора"
                )
        return value

    def update(self, instance, validated_data):
        """Обновление пользователя с обработкой пароля"""
        password = validated_data.pop("password", None)
        validated_data.pop("password2", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Если есть новый пароль - устанавливаем его
        if password:
            instance.set_password(password)

        instance.save()
        return instance
