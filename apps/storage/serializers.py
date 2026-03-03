import logging
import os
import uuid

from django.conf import settings
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import UserFile
from .validators import validate_unique_filename, FileValidator

logger = logging.getLogger(__name__)


class FileListSerializer(serializers.ModelSerializer):
    owner = UserSerializer(source="user", read_only=True)
    download_url = serializers.SerializerMethodField()
    view_url = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    size_display = serializers.SerializerMethodField()

    class Meta:
        model = UserFile
        fields = [
            "id",
            "original_name",
            "size",
            "size_display",
            "upload_date",
            "last_download",
            "comment",
            "owner",
            "share_token",
            "download_url",
            "view_url",
            "file_type",
        ]
        read_only_fields = [
            "id",
            "size",
            "size_display",
            "upload_date",
            "last_download",
            "owner",
            "share_token",
            "download_url",
            "view_url",
            "file_type",
        ]

    def get_download_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/api/storage/{obj.id}/download/")
        return None

    def get_view_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/api/storage/{obj.id}/view/")
        return None

    def get_file_type(self, obj):
        return (
            os.path.splitext(obj.original_name)[1][1:].lower()
            if obj.original_name
            else None
        )

    def get_size_display(self, obj):
        return obj.size_display


class FileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        write_only=True, required=True, validators=[FileValidator()]
    )

    class Meta:
        model = UserFile
        fields = ["file", "id", "original_name", "size", "comment"]
        extra_kwargs = {"comment": {"required": False, "allow_blank": True}}

    def validate(self, data):
        """Дополнительная валидация"""
        file = data.get("file")
        user = self.context["request"].user

        # Проверка уникальности имени
        unique_name = validate_unique_filename(user, file.name)
        data["unique_name"] = unique_name

        return data

    def create(self, validated_data):
        file = validated_data.pop("file")
        user = self.context["request"].user
        unique_name = validated_data.pop("unique_name", file.name)

        # Генерация пути для файла
        ext = os.path.splitext(file.name)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        relative_path = os.path.join(user.storage_path, unique_filename)
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # Создание директории
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Сохранение файла
        with open(full_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Создание записи в БД
        user_file = UserFile.objects.create(
            user=user,
            original_name=unique_name,
            size=file.size,
            file_path=relative_path,
            comment=validated_data.get("comment", ""),
        )

        logger.info(f"Файл загружен: {unique_name}, пользователь: {user.username}")
        return user_file


class FileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFile
        fields = ["original_name", "comment"]
        extra_kwargs = {
            "original_name": {"required": False},
            "comment": {"required": False},
        }

    def validate_original_name(self, value):
        if "." not in value:
            raise serializers.ValidationError("Имя файла должно содержать расширение")

        # Проверка уникальности имени для пользователя
        user_files = UserFile.objects.filter(user=self.context["request"].user).exclude(
            pk=self.instance.pk
        )

        if user_files.filter(original_name=value).exists():
            base, ext = os.path.splitext(value)
            counter = 1
            while user_files.filter(original_name=f"{base}_{counter:03}{ext}").exists():
                counter += 1
            value = f"{base}_{counter:03}{ext}"

        return value


class FileShareSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()
    share_token = serializers.CharField(read_only=True)

    class Meta:
        model = UserFile
        fields = ["share_token", "share_url", "share_token_created"]
        read_only_fields = ["share_token", "share_url", "share_token_created"]

    def get_share_url(self, obj):
        request = self.context.get("request")
        if request and obj.share_token:
            return request.build_absolute_uri(f"/api/storage/share/{obj.share_token}/")
        return None
