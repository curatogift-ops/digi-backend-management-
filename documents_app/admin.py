from django.contrib import admin
from documents_app.models import CommunicationLog, Document

admin.site.register(Document)
admin.site.register(CommunicationLog)
