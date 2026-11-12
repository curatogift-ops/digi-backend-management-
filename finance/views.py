from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import CanViewCompanyFinance, IsOwner, IsOwnerOrProjectManager
from activity.models import log_activity, notify_owners, notify_user
from finance.models import Expense, Invoice, Payment
from finance.serializers import ExpenseSerializer, InvoiceSerializer, PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'method', 'client', 'project']
    search_fields = ['payment_id', 'transaction_reference', 'client__client_name', 'project__name']

    def get_queryset(self):
        qs = Payment.objects.select_related('client', 'project', 'submitted_by', 'verified_by')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(Q(project__assigned_pm=user) | Q(submitted_by=user))
        return qs

    def perform_create(self, serializer):
        payment = serializer.save(
            submitted_by=self.request.user,
            status=Payment.Status.PENDING,
        )
        notify_owners(
            'Payment awaiting verification',
            f'{payment.payment_id} – ₹{payment.amount} for {payment.project.name}',
            f'/payments/{payment.id}',
            'Payment',
            payment.id,
        )
        log_activity(self.request.user, 'payment_submitted', 'Payment', payment.payment_id, request=self.request)

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        if self.action in ('create', 'update', 'partial_update'):
            # Allow status only for owners via verify/reject actions
            pass
        return serializer

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def verify(self, request, pk=None):
        payment = self.get_object()
        if payment.status != Payment.Status.PENDING:
            return Response({'detail': 'Only pending payments can be verified.'}, status=400)
        payment.verify(request.user, request.data.get('notes', ''))
        if payment.submitted_by:
            notify_user(payment.submitted_by, 'Payment verified', f'{payment.payment_id} verified', f'/payments/{payment.id}')
        log_activity(request.user, 'payment_verified', 'Payment', payment.payment_id, request=request)
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def reject(self, request, pk=None):
        payment = self.get_object()
        payment.reject(request.user, request.data.get('notes', ''))
        if payment.submitted_by:
            notify_user(payment.submitted_by, 'Payment rejected', f'{payment.payment_id}', f'/payments/{payment.id}')
        log_activity(request.user, 'payment_rejected', 'Payment', payment.payment_id, request=request)
        return Response(PaymentSerializer(payment).data)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'category', 'project']
    search_fields = ['expense_id', 'title', 'notes']

    def get_queryset(self):
        qs = Expense.objects.select_related('submitted_by', 'project')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(submitted_by=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)

    def get_permissions(self):
        if self.action in ('list',) and self.request.user.is_authenticated and not self.request.user.is_owner:
            # PM can list own expenses only (handled in queryset)
            return [IsOwnerOrProjectManager()]
        return super().get_permissions()


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'client', 'project']
    search_fields = ['invoice_number', 'client__client_name']

    def get_queryset(self):
        qs = Invoice.objects.select_related('client', 'project')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(project__assigned_pm=user)
        return qs

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only Owner can create invoices.')
        serializer.save(created_by=self.request.user)


@api_view(['GET'])
@permission_classes([CanViewCompanyFinance])
def accounts_dashboard(request):
    today = timezone.now().date()
    verified = Payment.objects.filter(status=Payment.Status.VERIFIED)
    total_collections = verified.aggregate(s=Sum('amount'))['s'] or 0
    from crm.models import Project
    total_project_value = Project.objects.aggregate(s=Sum('project_value'))['s'] or 0
    total_expenses = Expense.objects.filter(status__in=['approved', 'paid']).aggregate(s=Sum('amount'))['s'] or 0
    monthly = (
        verified.filter(payment_date__year=today.year, payment_date__month=today.month)
        .aggregate(s=Sum('amount'))['s'] or 0
    )
    return Response({
        'total_business_revenue': float(total_collections),
        'total_company_collections': float(total_collections),
        'total_outstanding': float(total_project_value) - float(total_collections),
        'monthly_income': float(monthly),
        'total_expenses': float(total_expenses),
        'net_cash_movement': float(total_collections) - float(total_expenses),
        'contracted_project_value': float(total_project_value),
        'invoices_issued': Invoice.objects.count(),
        'invoice_total': float(Invoice.objects.aggregate(s=Sum('total_amount'))['s'] or 0),
        'pending_verifications': Payment.objects.filter(status=Payment.Status.PENDING).count(),
    })
