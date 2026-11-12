from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner / Super Admin'
        PROJECT_MANAGER = 'project_manager', 'Employee / Project Manager'
        DEVELOPER = 'developer', 'Developer'

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.PROJECT_MANAGER)
    phone = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    is_active_employee = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER or self.is_superuser

    @property
    def is_project_manager(self):
        return self.role == self.Role.PROJECT_MANAGER

    @property
    def display_name(self):
        return self.get_full_name() or self.username
