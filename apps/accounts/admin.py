from django.contrib import admin

from .models import User


@admin.register(User)
class SimpleUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'full_name', 'is_admin', 'is_active']
    search_fields = ['username', 'email']
    list_filter = ['is_admin', 'is_active']
