from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_active_employee')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('CRM Profile', {'fields': ('role', 'phone', 'alternate_phone', 'designation', 'is_active_employee', 'avatar')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('CRM Profile', {'fields': ('role', 'phone', 'designation')}),
    )
