import logging

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator, MinLengthValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User

logger = logging.getLogger(__name__)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message="Пользователь с таким email уже существует"
        )]
    )

    class Meta:
        model = User
        fields = ["username", "email", "full_name", "password", "password2"]
        extra_kwargs = {
            "username": {"required": True, "validators": [MinLengthValidator(3)]},
            "email": {"required": True, "validators": [EmailValidator()]},
            "full_name": {"required": True, "validators": [MinLengthValidator(2)]},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        logger.info(f"Создан новый пользователь: {user.username}")
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


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе"""

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
        ]
        read_only_fields = ["id", "storage_path", "date_joined"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления пользователя (только для админа)"""

    class Meta:
        model = User
        fields = ["username", "email", "full_name", "is_admin"]
        extra_kwargs = {
            "username": {"required": False},
            "email": {"required": False},
            "full_name": {"required": False},
            "is_admin": {"required": False},
        }
