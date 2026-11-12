from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import ChangePasswordView, EmployeeViewSet, LoginView, MeView, health
from activity.views import (
    ActivityLogViewSet, ApprovalRequestViewSet, ExportRequestViewSet,
    NotificationViewSet, SystemSettingViewSet,
)
from crm.reports import reports
from crm.views import (
    ClientViewSet, FollowUpViewSet, LeadViewSet, PendingWorkViewSet,
    ProjectViewSet, RequirementViewSet, TaskViewSet, dashboard, global_search,
)
from documents_app.views import CommunicationLogViewSet, DocumentViewSet
from finance.views import ExpenseViewSet, InvoiceViewSet, PaymentViewSet, accounts_dashboard

router = DefaultRouter()
router.register('employees', EmployeeViewSet, basename='employee')
router.register('leads', LeadViewSet, basename='lead')
router.register('clients', ClientViewSet, basename='client')
router.register('requirements', RequirementViewSet, basename='requirement')
router.register('projects', ProjectViewSet, basename='project')
router.register('tasks', TaskViewSet, basename='task')
router.register('pending-work', PendingWorkViewSet, basename='pending-work')
router.register('followups', FollowUpViewSet, basename='followup')
router.register('payments', PaymentViewSet, basename='payment')
router.register('expenses', ExpenseViewSet, basename='expense')
router.register('invoices', InvoiceViewSet, basename='invoice')
router.register('documents', DocumentViewSet, basename='document')
router.register('communications', CommunicationLogViewSet, basename='communication')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('activity-logs', ActivityLogViewSet, basename='activity-log')
router.register('approvals', ApprovalRequestViewSet, basename='approval')
router.register('exports', ExportRequestViewSet, basename='export')
router.register('settings', SystemSettingViewSet, basename='setting')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', MeView.as_view(), name='me'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('api/dashboard/', dashboard, name='dashboard'),
    path('api/accounts-dashboard/', accounts_dashboard, name='accounts_dashboard'),
    path('api/reports/', reports, name='reports'),
    path('api/search/', global_search, name='search'),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'Digitech Avenue CRM'
admin.site.site_title = 'Digitech Avenue'
