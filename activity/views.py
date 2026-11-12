from datetime import timedelta
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsOwner, IsOwnerOrProjectManager
from activity.models import (
    ActivityLog, ApprovalRequest, ExportRequest, Notification, SystemSetting,
    log_activity, notify_owners, notify_user,
)
from activity.serializers import (
    ActivityLogSerializer, ApprovalRequestSerializer, ExportRequestSerializer,
    NotificationSerializer, SystemSettingSerializer,
)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'post', 'head', 'options']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'detail': 'All notifications marked as read.'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.save(update_fields=['is_read'])
        return Response(NotificationSerializer(n).data)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['action', 'model_name', 'user']
    search_fields = ['action', 'object_repr', 'object_id']

    def get_queryset(self):
        qs = ActivityLog.objects.select_related('user')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(user=user)
        return qs


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'action_type']

    def get_queryset(self):
        qs = ApprovalRequest.objects.select_related('requester', 'reviewed_by')
        if not self.request.user.is_owner:
            qs = qs.filter(requester=self.request.user)
        return qs

    def perform_create(self, serializer):
        req = serializer.save(requester=self.request.user)
        notify_owners(
            'Approval request pending',
            f'{req.request_id}: {req.get_action_type_display()} – {req.reason[:120]}',
            f'/approvals/{req.id}',
            'ApprovalRequest',
            req.id,
        )
        log_activity(self.request.user, 'approval_requested', 'ApprovalRequest', req.request_id, request=self.request)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def approve(self, request, pk=None):
        req = self.get_object()
        req.status = ApprovalRequest.Status.APPROVED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.expires_at = timezone.now() + timedelta(hours=1)
        req.owner_notes = request.data.get('notes', '')
        req.save()
        notify_user(req.requester, 'Approval granted', f'{req.request_id} approved (valid 1 hour)', f'/approvals/{req.id}')
        log_activity(request.user, 'approval_granted', 'ApprovalRequest', req.request_id, request=request)
        return Response(ApprovalRequestSerializer(req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def reject(self, request, pk=None):
        req = self.get_object()
        req.status = ApprovalRequest.Status.REJECTED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.owner_notes = request.data.get('notes', '')
        req.save()
        notify_user(req.requester, 'Approval rejected', f'{req.request_id}', f'/approvals/{req.id}')
        return Response(ApprovalRequestSerializer(req).data)


class ExportRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ExportRequestSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'export_type', 'format']

    def get_queryset(self):
        qs = ExportRequest.objects.select_related('requester', 'reviewed_by')
        if not self.request.user.is_owner:
            qs = qs.filter(requester=self.request.user)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_owner:
            export = serializer.save(requester=user, status=ExportRequest.Status.APPROVED, reviewed_by=user)
        else:
            export = serializer.save(requester=user)
            approval = ApprovalRequest.objects.create(
                requester=user,
                action_type=ApprovalRequest.ActionType.EXPORT_BULK,
                reason=export.reason,
                record_info={'export_type': export.export_type, 'export_id': export.export_id},
            )
            export.approval = approval
            export.save(update_fields=['approval'])
            notify_owners(
                'Export approval required',
                f'{export.export_id}: {export.export_type}',
                f'/exports/{export.id}',
                'ExportRequest',
                export.id,
            )
        log_activity(user, 'export_requested', 'ExportRequest', export.export_id, request=self.request)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def approve(self, request, pk=None):
        export = self.get_object()
        export.status = ExportRequest.Status.APPROVED
        export.reviewed_by = request.user
        export.save()
        if export.approval_id:
            export.approval.status = ApprovalRequest.Status.APPROVED
            export.approval.reviewed_by = request.user
            export.approval.reviewed_at = timezone.now()
            export.approval.expires_at = timezone.now() + timedelta(hours=1)
            export.approval.save()
        notify_user(export.requester, 'Export approved', f'{export.export_id}', f'/exports/{export.id}')
        return Response(ExportRequestSerializer(export).data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def reject(self, request, pk=None):
        export = self.get_object()
        export.status = ExportRequest.Status.REJECTED
        export.reviewed_by = request.user
        export.save()
        notify_user(export.requester, 'Export rejected', f'{export.export_id}', f'/exports/{export.id}')
        return Response(ExportRequestSerializer(export).data)


class SystemSettingViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsOwner]
    lookup_field = 'key'
