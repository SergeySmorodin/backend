import logging

from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра пользователя"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "is_admin",
            "storage_path",
            "date_joined",
            "last_login",
            "is_active",
        ]
        read_only_fields = ["id", "storage_path", "date_joined", "last_login", "is_active"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя (регистрация)"""

    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2", "full_name"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({
                "password": "Пароли не совпадают"
            })
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует"
            )
        return value

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
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
                raise serializers.ValidationError(
                    "Неверное имя пользователя или пароль"
                )
            if not user.is_active:
                raise serializers.ValidationError("Пользователь деактивирован")
        else:
            raise serializers.ValidationError(
                "Необходимо указать имя пользователя и пароль"
            )

        attrs["user"] = user
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка пользователей"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "is_admin",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления пользователя (PUT/PATCH)"""

    is_admin = serializers.BooleanField(required=False)
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={"input_type": "password"}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=False,
        style={"input_type": "password"}
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
                raise serializers.ValidationError({
                    "password": "Пароли не совпадают"
                })
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
        request = self.context.get('request')
        if request and not (request.user.is_staff or request.user.is_admin or request.user.is_superuser):
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
