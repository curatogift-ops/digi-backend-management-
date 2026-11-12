from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrProjectManager
from crm.models import Client, FollowUp, Lead, Project, Requirement, Task
from finance.models import Expense, Payment


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrProjectManager])
def reports(request):
    user = request.user
    today = timezone.now().date()

    if user.is_owner:
        leads = Lead.objects.all()
        confirmed = leads.filter(status=Lead.Status.CONFIRMED).count()
        lost = leads.filter(status=Lead.Status.LOST).count()
        total = leads.count() or 1
        verified = Payment.objects.filter(status=Payment.Status.VERIFIED).aggregate(s=Sum('amount'))['s'] or 0
        project_value = Project.objects.aggregate(s=Sum('project_value'))['s'] or 0
        expenses = Expense.objects.filter(status__in=['approved', 'paid']).aggregate(s=Sum('amount'))['s'] or 0
        return Response({
            'role': 'owner',
            'total_enquiries': leads.count(),
            'confirmed_projects': confirmed,
            'lost_leads': lost,
            'conversion_percentage': round((confirmed / total) * 100, 2),
            'total_project_value': float(project_value),
            'actual_collections': float(verified),
            'outstanding_amounts': float(project_value) - float(verified),
            'expenses': float(expenses),
            'cash_movement': float(verified) - float(expenses),
            'project_completion': Project.objects.filter(status=Project.Status.COMPLETED).count(),
            'service_wise': list(
                Project.objects.values('service_type').annotate(count=Count('id')).order_by('-count')
            ),
            'lead_sources': list(
                Lead.objects.values('lead_source').annotate(count=Count('id')).order_by('-count')
            ),
        })

    my_leads = Lead.objects.filter(Q(assigned_to=user) | Q(created_by=user))
    my_projects = Project.objects.filter(assigned_pm=user)
    my_tasks = Task.objects.filter(assigned_to=user)
    my_reqs = Requirement.objects.filter(created_by=user)
    return Response({
        'role': 'project_manager',
        'leads_handled': my_leads.count(),
        'followups_completed': FollowUp.objects.filter(employee=user, status='completed').count(),
        'requirements_submitted': my_reqs.exclude(status='draft').count(),
        'requirements_awaiting': my_reqs.filter(status='awaiting_approval').count(),
        'requirements_approved': my_reqs.filter(status='approved').count(),
        'projects_managed': my_projects.count(),
        'tasks_completed': my_tasks.filter(status='done').count(),
        'overdue_tasks': my_tasks.filter(due_date__lt=today).exclude(status='done').count(),
        'client_outstanding': [
            {
                'project': p.name,
                'client': p.client.client_name,
                'outstanding': float(p.outstanding_balance),
            }
            for p in my_projects
            if p.outstanding_balance > 0
        ],
    })
