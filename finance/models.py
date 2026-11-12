from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Payment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending_verification', 'Pending Verification'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'
        REFUNDED = 'refunded', 'Refunded'

    class Method(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        UPI = 'upi', 'UPI'
        CASH = 'cash', 'Cash'
        CHEQUE = 'cheque', 'Cheque'
        CARD = 'card', 'Card'
        OTHER = 'other', 'Other'

    payment_id = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey('crm.Client', on_delete=models.CASCADE, related_name='payments')
    project = models.ForeignKey('crm.Project', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=30, choices=Method.choices, default=Method.UPI)
    transaction_reference = models.CharField(max_length=255, blank=True)
    proof = models.FileField(upload_to='payment_proofs/', blank=True, null=True)
    collection_notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='submitted_payments'
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    correction_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'transaction_reference'],
                condition=~models.Q(transaction_reference=''),
                name='unique_project_txn_ref',
            )
        ]

    def save(self, *args, **kwargs):
        if not self.payment_id:
            last = Payment.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.payment_id = f'PY{n:05d}'
        super().save(*args, **kwargs)

    @transaction.atomic
    def verify(self, owner, notes=''):
        self.status = self.Status.VERIFIED
        self.verified_by = owner
        self.verified_at = timezone.now()
        self.correction_notes = notes
        self.save()

    @transaction.atomic
    def reject(self, owner, notes=''):
        self.status = self.Status.REJECTED
        self.verified_by = owner
        self.verified_at = timezone.now()
        self.correction_notes = notes
        self.save()

    def __str__(self):
        return f'{self.payment_id} – {self.amount}'


class Expense(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        PAID = 'paid', 'Paid'

    expense_id = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField(default=timezone.localdate)
    project = models.ForeignKey(
        'crm.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses'
    )
    notes = models.TextField(blank=True)
    receipt = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='submitted_expenses'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_expenses'
    )

    class Meta:
        ordering = ['-expense_date']

    def save(self, *args, **kwargs):
        if not self.expense_id:
            last = Expense.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.expense_id = f'EX{n:05d}'
        super().save(*args, **kwargs)


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        PARTIALLY_PAID = 'partially_paid', 'Partially Paid'
        PAID = 'paid', 'Paid'
        OVERDUE = 'overdue', 'Overdue'
        CANCELLED = 'cancelled', 'Cancelled'

    invoice_number = models.CharField(max_length=30, unique=True, blank=True)
    client = models.ForeignKey('crm.Client', on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(
        'crm.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices'
    )
    invoice_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_invoices'
    )

    class Meta:
        ordering = ['-invoice_date']

    @property
    def balance(self):
        return self.total_amount - self.paid_amount

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Invoice.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.invoice_number = f'INV{n:05d}'
        if not self.total_amount:
            self.total_amount = self.taxable_amount + self.tax_amount
        super().save(*args, **kwargs)
