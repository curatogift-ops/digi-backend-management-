from rest_framework import serializers
from activity.models import ActivityLog, ApprovalRequest, ExportRequest, Notification, SystemSetting


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.display_name', read_only=True, default='')

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_name', 'action', 'model_name', 'object_id',
            'object_repr', 'old_values', 'new_values', 'ip_address', 'created_at',
        ]
        read_only_fields = fields


class ApprovalRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.display_name', read_only=True, default='')
    action_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = '__all__'
        read_only_fields = [
            'request_id', 'requester', 'status', 'otp_hash', 'reviewed_by',
            'reviewed_at', 'expires_at', 'created_at', 'updated_at',
        ]


class ExportRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.display_name', read_only=True, default='')

    class Meta:
        model = ExportRequest
        fields = '__all__'
        read_only_fields = [
            'export_id', 'requester', 'status', 'approval', 'reviewed_by',
            'file', 'created_at', 'updated_at',
        ]


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = '__all__'
