from django.contrib import admin
from finance.models import Expense, Invoice, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'client', 'project', 'amount', 'status', 'payment_date')
    list_filter = ('status', 'method')


admin.site.register(Expense)
admin.site.register(Invoice)
