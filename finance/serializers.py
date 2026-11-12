from rest_framework import serializers
from finance.models import Expense, Invoice, Payment


class PaymentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.display_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = [
            'payment_id', 'submitted_by', 'verified_by', 'verified_at',
            'status', 'created_at', 'updated_at',
        ]


class ExpenseSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.CharField(source='submitted_by.display_name', read_only=True, default='')
    project_name = serializers.CharField(source='project.name', read_only=True, default='')

    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['expense_id', 'submitted_by', 'reviewed_by', 'created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default='')
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'created_by', 'created_at', 'updated_at']
