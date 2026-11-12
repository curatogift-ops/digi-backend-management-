from rest_framework import serializers
from documents_app.models import CommunicationLog, Document


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.display_name', read_only=True, default='')
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            if obj.is_sensitive and not request.user.is_owner:
                return None
            return request.build_absolute_uri(obj.file.url)
        return None


class CommunicationLogSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.display_name', read_only=True, default='')
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = CommunicationLog
        fields = '__all__'
        read_only_fields = ['author', 'created_at', 'updated_at']
