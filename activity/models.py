from django.conf import settings
from django.db import models
from django.utils import timezone
import secrets


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Notification(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    related_model = models.CharField(max_length=100, blank=True)
    related_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='activity_logs'
    )
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} by {self.user} at {self.created_at}'


class ApprovalRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EXPIRED = 'expired', 'Expired'
        USED = 'used', 'Used'

    class ActionType(models.TextChoices):
        EXPORT_CLIENTS = 'export_clients', 'Export Client Database'
        EXPORT_FINANCIAL = 'export_financial', 'Export Financial Records'
        EXPORT_BULK = 'export_bulk', 'Export Bulk Client Info'
        DELETE_RECORD = 'delete_record', 'Permanent Deletion'
        EDIT_VERIFIED_PAYMENT = 'edit_verified_payment', 'Edit Verified Payment'
        DOWNLOAD_SENSITIVE = 'download_sensitive', 'Download Restricted Document'
        CHANGE_PERMISSIONS = 'change_permissions', 'Change Permissions'
        ACCESS_RESTRICTED_REPORT = 'access_restricted_report', 'Access Restricted Report'
        OTHER = 'other', 'Other Sensitive Action'

    request_id = models.CharField(max_length=20, unique=True, blank=True)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='approval_requests'
    )
    action_type = models.CharField(max_length=40, choices=ActionType.choices)
    reason = models.TextField()
    record_info = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    otp_hash = models.CharField(max_length=128, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_approvals'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    owner_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.request_id:
            last = ApprovalRequest.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.request_id = f'AP{n:05d}'
        super().save(*args, **kwargs)

    def is_valid_for_use(self):
        if self.status != self.Status.APPROVED:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status'])
            return False
        return True


class ExportRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'

    class Format(models.TextChoices):
        CSV = 'csv', 'CSV'
        EXCEL = 'excel', 'Excel'
        PDF = 'pdf', 'PDF'

    export_id = models.CharField(max_length=20, unique=True, blank=True)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='export_requests'
    )
    export_type = models.CharField(max_length=100)
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.CSV)
    reason = models.TextField()
    filters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approval = models.ForeignKey(
        ApprovalRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='exports'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_exports'
    )
    file = models.FileField(upload_to='exports/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.export_id:
            last = ExportRequest.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.export_id = f'EP{n:05d}'
        super().save(*args, **kwargs)


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.key


def log_activity(user, action, model_name='', object_id='', object_repr='', old_values=None, new_values=None, request=None):
    ip = None
    if request:
        ip = request.META.get('REMOTE_ADDR')
    return ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else '',
        object_repr=object_repr[:255] if object_repr else '',
        old_values=old_values or {},
        new_values=new_values or {},
        ip_address=ip,
    )


def notify_user(user, title, message='', link='', related_model='', related_id=None):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link,
        related_model=related_model,
        related_id=related_id,
    )


def notify_owners(title, message='', link='', related_model='', related_id=None):
    from accounts.models import User
    owners = User.objects.filter(role=User.Role.OWNER, is_active=True)
    for owner in owners:
        notify_user(owner, title, message, link, related_model, related_id)
