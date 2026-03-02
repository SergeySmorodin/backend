import logging
import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrSelf
from .models import UserFile
from .serializers import (
    FileListSerializer,
    FileUploadSerializer,
    FileUpdateSerializer,
    FileShareSerializer
)

logger = logging.getLogger(__name__)


class FileViewSet(viewsets.ModelViewSet):
    queryset = UserFile.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return FileUploadSerializer
        elif self.action in ['update', 'partial_update']:
            return FileUpdateSerializer
        elif self.action == 'share':
            return FileShareSerializer
        return FileListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        target_user_id = self.request.query_params.get('user_id')

        # Администратор может видеть файлы любого пользователя
        if user.is_admin and target_user_id:
            queryset = queryset.filter(user_id=target_user_id)
        elif not user.is_admin:
            queryset = queryset.filter(user=user)

        logger.info(f"Получен список файлов для пользователя {user.id}")
        return queryset.select_related('user')

    def perform_create(self, serializer):

        serializer.save()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        try:
            file_obj = self.get_object()

            if not file_obj.exists:
                raise Http404("Файл не найден на сервере")

            # Обновление даты скачивания
            file_obj.update_download_date()

            response = FileResponse(
                open(file_obj.full_path, 'rb'),
                as_attachment=True,
                filename=file_obj.original_name
            )

            logger.info(f"Файл {file_obj.id} скачан пользователем {request.user.id}")
            return response

        except Http404:
            return Response(
                {"error": "Файл не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла: {str(e)}")
            return Response(
                {"error": "Не удалось загрузить файл"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def view(self, request, pk=None):
        try:
            file_obj = self.get_object()

            if not file_obj.exists:
                raise Http404("Файл не найден на сервере")

            # Определение MIME-типа
            content_type, _ = mimetypes.guess_type(file_obj.original_name)
            if not content_type:
                content_type = 'application/octet-stream'

            response = FileResponse(
                open(file_obj.full_path, 'rb'),
                content_type=content_type
            )
            response['Content-Disposition'] = f'inline; filename="{file_obj.original_name}"'

            return response

        except Http404:
            return Response(
                {"error": "Файл не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Ошибка при просмотре файла: {str(e)}")
            return Response(
                {"error": "Не удалось просмотреть файл"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Создание или обновление ссылки для общего доступа"""
        try:
            file_obj = self.get_object()

            # Генерация нового токена
            file_obj.regenerate_share_token()

            serializer = self.get_serializer(file_obj)
            logger.info(f"Создана ссылка для файла {file_obj.id} пользователем {request.user.id}")

            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Ошибка при создании ссылки: {str(e)}")
            return Response(
                {"error": "Не удалось создать ссылку"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def revoke_share(self, request, pk=None):
        """Отзыв ссылки для общего доступа"""

        try:
            file_obj = self.get_object()
            file_obj.share_token = None
            file_obj.share_token_created = None
            file_obj.save(update_fields=['share_token', 'share_token_created'])

            logger.info(f"Отозвана ссылка для файла {file_obj.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Ошибка при отзыве ссылки: {str(e)}")
            return Response(
                {"error": "Не удалось отозвать ссылку"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            file_obj = self.get_object()
            file_path = file_obj.full_path
            file_dir = os.path.dirname(file_path)

            file_obj.delete()

            # Удаление пустых директорий
            self._remove_empty_dirs(file_dir)

            logger.info(f"Файл {file_obj.id} удален пользователем {request.user.id}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Ошибка при удалении файла: {str(e)}")
            return Response(
                {"error": "Не удалось удалить файл"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _remove_empty_dirs(self, current_dir):
        """Рекурсивное удаление пустых директорий"""

        media_root = settings.MEDIA_ROOT
        current_dir = os.path.abspath(current_dir)
        media_root = os.path.abspath(media_root)

        if not current_dir.startswith(media_root):
            return

        while current_dir != media_root:
            try:
                if not os.listdir(current_dir):
                    os.rmdir(current_dir)
                    logger.info(f"Удалена пустая директория: {current_dir}")
                    current_dir = os.path.dirname(current_dir)
                else:
                    break
            except OSError as e:
                logger.warning(f"Не удалось удалить директорию {current_dir}: {str(e)}")
                break


class FileShareDownloadViewSet(viewsets.ViewSet):
    """ViewSet для скачивания файлов по публичным ссылкам"""

    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, share_token=None):
        try:
            file_obj = get_object_or_404(UserFile, share_token=share_token)

            if request.query_params.get('info') == 'true':
                serializer = FileShareSerializer(file_obj, context={'request': request})
                return Response(serializer.data)

            if not file_obj.exists:
                raise Http404("Файл не найден на сервере")

            file_obj.update_download_date()

            response = FileResponse(
                open(file_obj.full_path, 'rb'),
                as_attachment=True,
                filename=file_obj.original_name
            )

            logger.info(f"Файл {file_obj.id} скачан по публичной ссылке")
            return response

        except UserFile.DoesNotExist:
            return Response(
                {"error": "Ссылка недействительна"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Ошибка при скачивании по ссылке: {str(e)}")
            return Response(
                {"error": "Не удалось загрузить файл"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
