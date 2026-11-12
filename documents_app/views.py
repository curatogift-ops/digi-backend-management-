from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from accounts.permissions import IsOwnerOrProjectManager
from activity.models import log_activity
from documents_app.models import CommunicationLog, Document
from documents_app.serializers import CommunicationLogSerializer, DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['category', 'client', 'project', 'is_sensitive']
    search_fields = ['title', 'notes']

    def get_queryset(self):
        qs = Document.objects.select_related('uploaded_by', 'client', 'project')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(is_sensitive=False)
        return qs

    def perform_create(self, serializer):
        doc = serializer.save(uploaded_by=self.request.user)
        log_activity(self.request.user, 'document_uploaded', 'Document', doc.id, doc.title, request=self.request)

    def retrieve(self, request, *args, **kwargs):
        doc = self.get_object()
        if doc.is_sensitive and not request.user.is_owner:
            raise PermissionDenied('Sensitive document requires Owner access or approved export.')
        return super().retrieve(request, *args, **kwargs)


class CommunicationLogViewSet(viewsets.ModelViewSet):
    serializer_class = CommunicationLogSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['type', 'client', 'project']
    search_fields = ['subject', 'content']

    def get_queryset(self):
        return CommunicationLog.objects.select_related('author', 'client', 'project')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
