from django.contrib import admin
from .models import UserFile


@admin.register(UserFile)
class UserFileAdmin(admin.ModelAdmin):
    """Админ-панель для модели файлов"""

    list_display = [
        "original_name",
        "user",
        "size",
        "upload_date",
        "last_download",
    ]

    list_filter = [
        "upload_date",
        "user",
    ]

    search_fields = [
        "original_name",
        "user__username",
    ]

    readonly_fields = [
        "size",
        "upload_date",
        "last_download",
        "share_token",
        "share_token_created",
    ]

    fieldsets = (
        ("Основная информация", {"fields": ("original_name", "user", "comment")}),
        (
            "Данные файла",
            {"fields": ("size", "upload_date", "last_download", "file_path")},
        ),
        (
            "Ссылка для доступа",
            {
                "fields": ("share_token", "share_token_created"),
                "classes": ("collapse",),
            },
        ),
    )
