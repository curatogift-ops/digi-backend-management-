from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Document(TimeStampedModel):
    class Category(models.TextChoices):
        CLIENT_INFO = 'client_info', 'Client Information'
        REQUIREMENTS = 'requirements', 'Requirements'
        PROPOSAL = 'proposal', 'Proposal'
        QUOTATION = 'quotation', 'Quotation'
        AGREEMENT = 'agreement', 'Agreement'
        UIUX = 'uiux', 'UI/UX'
        DEVELOPMENT = 'development', 'Development'
        TESTING = 'testing', 'Testing'
        INVOICE = 'invoice', 'Invoice'
        RECEIPT = 'receipt', 'Receipt'
        FINAL_DELIVERY = 'final_delivery', 'Final Delivery'
        OTHER = 'other', 'Other'

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=40, choices=Category.choices, default=Category.OTHER)
    client = models.ForeignKey(
        'crm.Client', on_delete=models.CASCADE, related_name='documents', null=True, blank=True
    )
    project = models.ForeignKey(
        'crm.Project', on_delete=models.CASCADE, related_name='documents', null=True, blank=True
    )
    file = models.FileField(upload_to='documents/')
    is_sensitive = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CommunicationLog(TimeStampedModel):
    class Type(models.TextChoices):
        CALL = 'call', 'Call Notes'
        MEETING = 'meeting', 'Meeting Notes'
        WHATSAPP = 'whatsapp', 'WhatsApp Summary'
        EMAIL = 'email', 'Email Notes'
        FEEDBACK = 'feedback', 'Client Feedback'
        DECISION = 'decision', 'Decision'
        FOLLOWUP = 'followup', 'Follow-up Outcome'
        OTHER = 'other', 'Other'

    client = models.ForeignKey('crm.Client', on_delete=models.CASCADE, related_name='communications')
    project = models.ForeignKey(
        'crm.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='communications'
    )
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.CALL)
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='communications'
    )

    class Meta:
        ordering = ['-created_at']
