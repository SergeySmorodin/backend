import logging

from django.http import FileResponse, Http404
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
