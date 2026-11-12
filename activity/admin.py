from django.contrib import admin
from activity.models import ActivityLog, ApprovalRequest, ExportRequest, Notification, SystemSetting


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'model_name', 'object_id', 'created_at')
    readonly_fields = [f.name for f in ActivityLog._meta.fields]


admin.site.register(Notification)
admin.site.register(ApprovalRequest)
admin.site.register(ExportRequest)
admin.site.register(SystemSetting)
