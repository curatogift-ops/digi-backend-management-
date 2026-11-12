from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsOwner, IsOwnerOrProjectManager
from activity.models import log_activity, notify_owners, notify_user
from crm.models import (
    Client, FollowUp, Lead, Milestone, PendingWork, Project, ProjectMember, Requirement, Task,
)
from crm.serializers import (
    ClientDetailSerializer, ClientSerializer, FollowUpSerializer, LeadSerializer,
    MilestoneSerializer, PendingWorkSerializer, ProjectListSerializer, ProjectMemberSerializer,
    ProjectSerializer, RequirementSerializer, TaskSerializer,
)


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'priority', 'assigned_to', 'lead_source']
    search_fields = ['lead_id', 'client_name', 'company', 'phone', 'email', 'contact_person']
    ordering_fields = ['enquiry_date', 'estimated_value', 'created_at', 'priority']

    def get_queryset(self):
        qs = Lead.objects.select_related('assigned_to', 'created_by')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(Q(assigned_to=user) | Q(created_by=user))
        return qs

    def perform_create(self, serializer):
        lead = serializer.save(created_by=self.request.user)
        if not lead.assigned_to:
            lead.assigned_to = self.request.user
            lead.save(update_fields=['assigned_to'])
        log_activity(self.request.user, 'lead_created', 'Lead', lead.lead_id, str(lead), request=self.request)
        if lead.assigned_to and lead.assigned_to != self.request.user:
            notify_user(lead.assigned_to, 'New lead assigned', f'{lead.lead_id} – {lead.client_name}', f'/leads/{lead.id}')

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        lead = self.get_object()
        if lead.converted_client_id:
            return Response({'detail': 'Lead already converted.'}, status=400)
        client = Client.objects.create(
            client_name=lead.client_name,
            company_name=lead.company,
            contact_person=lead.contact_person or lead.client_name,
            phone=lead.phone,
            email=lead.email,
            location=lead.location,
            business_type=lead.business_type,
            lead_source=lead.lead_source,
            assigned_pm=lead.assigned_to or request.user,
            notes=lead.notes,
            created_by=request.user,
        )
        lead.status = Lead.Status.CONFIRMED
        lead.converted_client = client
        lead.save()
        log_activity(request.user, 'lead_converted', 'Lead', lead.lead_id, str(client), request=request)
        return Response(ClientSerializer(client).data, status=201)


class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'assigned_pm', 'industry']
    search_fields = ['client_id', 'client_name', 'company_name', 'phone', 'email', 'contact_person']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClientDetailSerializer
        return ClientSerializer

    def get_queryset(self):
        qs = Client.objects.select_related('assigned_pm', 'created_by').prefetch_related('projects')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(Q(assigned_pm=user) | Q(created_by=user))
        return qs

    def perform_create(self, serializer):
        client = serializer.save(created_by=self.request.user)
        if not client.assigned_pm:
            client.assigned_pm = self.request.user
            client.save(update_fields=['assigned_pm'])
        log_activity(self.request.user, 'client_created', 'Client', client.client_id, str(client), request=self.request)


class RequirementViewSet(viewsets.ModelViewSet):
    serializer_class = RequirementSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'client', 'created_by']
    search_fields = ['requirement_id', 'client__client_name', 'solution_type']

    def get_queryset(self):
        qs = Requirement.objects.select_related('client', 'created_by', 'reviewed_by')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(Q(created_by=user) | Q(client__assigned_pm=user))
        return qs

    def perform_create(self, serializer):
        req = serializer.save(created_by=self.request.user)
        log_activity(self.request.user, 'requirement_created', 'Requirement', req.requirement_id, str(req), request=self.request)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        req = self.get_object()
        if req.status not in (Requirement.Status.DRAFT, Requirement.Status.CHANGES_REQUESTED):
            return Response({'detail': 'Cannot submit in current status.'}, status=400)
        req.status = Requirement.Status.AWAITING_APPROVAL
        req.submitted_at = timezone.now()
        req.save()
        notify_owners(
            'Requirement awaiting approval',
            f'{req.requirement_id} for {req.client.client_name}',
            f'/requirements/{req.id}',
            'Requirement',
            req.id,
        )
        log_activity(request.user, 'requirement_submitted', 'Requirement', req.requirement_id, request=request)
        return Response(RequirementSerializer(req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def approve(self, request, pk=None):
        req = self.get_object()
        req.status = Requirement.Status.APPROVED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.owner_comments = request.data.get('comments', req.owner_comments)
        req.save()
        if req.created_by:
            notify_user(req.created_by, 'Requirement approved', f'{req.requirement_id} approved', f'/requirements/{req.id}')
        log_activity(request.user, 'requirement_approved', 'Requirement', req.requirement_id, request=request)
        return Response(RequirementSerializer(req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def request_changes(self, request, pk=None):
        req = self.get_object()
        req.status = Requirement.Status.CHANGES_REQUESTED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.owner_comments = request.data.get('comments', '')
        req.save()
        if req.created_by:
            notify_user(req.created_by, 'Changes requested', f'{req.requirement_id}: {req.owner_comments}', f'/requirements/{req.id}')
        return Response(RequirementSerializer(req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def reject(self, request, pk=None):
        req = self.get_object()
        req.status = Requirement.Status.REJECTED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.owner_comments = request.data.get('comments', '')
        req.save()
        if req.created_by:
            notify_user(req.created_by, 'Requirement rejected', f'{req.requirement_id}', f'/requirements/{req.id}')
        return Response(RequirementSerializer(req).data)

    @action(detail=True, methods=['post'])
    def create_project(self, request, pk=None):
        req = self.get_object()
        if req.status != Requirement.Status.APPROVED:
            return Response({'detail': 'Requirement must be approved first.'}, status=400)
        project = Project.objects.create(
            client=req.client,
            requirement=req,
            name=request.data.get('name') or f'{req.client.client_name} – {req.solution_type or "Project"}',
            service_type=req.solution_type,
            approved_scope=req.essential_features or req.detailed_features,
            project_value=req.estimated_value,
            assigned_pm=req.client.assigned_pm or request.user,
            start_date=timezone.now().date(),
            status=Project.Status.PLANNING,
            created_by=request.user,
        )
        log_activity(request.user, 'project_created_from_requirement', 'Project', project.project_id, request=request)
        return Response(ProjectSerializer(project).data, status=201)


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'priority', 'assigned_pm', 'client', 'service_type']
    search_fields = ['project_id', 'name', 'client__client_name', 'client__client_id']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer

    def get_queryset(self):
        qs = Project.objects.select_related('client', 'assigned_pm', 'requirement').prefetch_related('members', 'milestones')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(Q(assigned_pm=user) | Q(members__user=user) | Q(created_by=user)).distinct()
        return qs

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)
        log_activity(self.request.user, 'project_created', 'Project', project.project_id, str(project), request=self.request)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get('user')
        role_label = request.data.get('role_label', '')
        member, _ = ProjectMember.objects.get_or_create(project=project, user_id=user_id, defaults={'role_label': role_label})
        return Response(ProjectMemberSerializer(member).data)

    @action(detail=True, methods=['post'])
    def add_milestone(self, request, pk=None):
        project = self.get_object()
        serializer = MilestoneSerializer(data={**request.data, 'project': project.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'priority', 'assigned_to', 'project', 'client']
    search_fields = ['task_id', 'title', 'description']

    def get_queryset(self):
        qs = Task.objects.select_related('assigned_to', 'project', 'client')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(Q(assigned_to=user) | Q(created_by=user) | Q(project__assigned_pm=user))
        return qs

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user)
        if task.assigned_to:
            notify_user(task.assigned_to, 'Task assigned', task.title, f'/tasks/{task.id}')
        log_activity(self.request.user, 'task_created', 'Task', task.task_id, str(task), request=self.request)


class PendingWorkViewSet(viewsets.ModelViewSet):
    serializer_class = PendingWorkSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['category', 'priority', 'project', 'client', 'responsible']
    search_fields = ['description', 'next_action']

    def get_queryset(self):
        return PendingWork.objects.select_related('responsible', 'project', 'client')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FollowUpViewSet(viewsets.ModelViewSet):
    serializer_class = FollowUpSerializer
    permission_classes = [IsOwnerOrProjectManager]
    filterset_fields = ['status', 'method', 'employee', 'client', 'lead', 'project']
    search_fields = ['discussion_notes', 'outcome', 'client__client_name']

    def get_queryset(self):
        qs = FollowUp.objects.select_related('employee', 'client', 'lead', 'project')
        user = self.request.user
        if not user.is_owner:
            qs = qs.filter(employee=user)
        return qs

    def perform_create(self, serializer):
        employee = serializer.validated_data.get('employee') or self.request.user
        serializer.save(employee=employee)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    now = timezone.now()

    if user.is_owner:
        leads = Lead.objects.all()
        projects = Project.objects.all()
        from finance.models import Payment, Expense

        verified = Payment.objects.filter(status=Payment.Status.VERIFIED).aggregate(s=Sum('amount'))['s'] or 0
        project_value = projects.aggregate(s=Sum('project_value'))['s'] or 0
        expenses = Expense.objects.filter(status__in=['approved', 'paid']).aggregate(s=Sum('amount'))['s'] or 0
        outstanding = project_value - verified

        data = {
            'role': 'owner',
            'metrics': {
                'total_leads': leads.count(),
                'new_leads': leads.filter(status=Lead.Status.NEW).count(),
                'confirmed_projects': projects.exclude(status=Project.Status.CANCELLED).count(),
                'active_projects': projects.filter(
                    status__in=[
                        Project.Status.PLANNING, Project.Status.UIUX, Project.Status.DEVELOPMENT,
                        Project.Status.INTERNAL_TESTING, Project.Status.CLIENT_REVIEW, Project.Status.REVISIONS,
                    ]
                ).count(),
                'completed_projects': projects.filter(status=Project.Status.COMPLETED).count(),
                'on_hold_projects': projects.filter(status=Project.Status.ON_HOLD).count(),
                'total_project_value': float(project_value),
                'total_revenue': float(verified),
                'total_outstanding': float(outstanding),
                'monthly_expenses': float(
                    Expense.objects.filter(
                        expense_date__year=today.year, expense_date__month=today.month
                    ).aggregate(s=Sum('amount'))['s'] or 0
                ),
                'net_cash_movement': float(verified) - float(expenses),
            },
            'action_centre': {
                'requirements_awaiting': Requirement.objects.filter(status=Requirement.Status.AWAITING_APPROVAL).count(),
                'payments_pending': Payment.objects.filter(status=Payment.Status.PENDING).count(),
                'export_requests': __import__('activity.models', fromlist=['ExportRequest']).ExportRequest.objects.filter(status='pending').count(),
                'overdue_tasks': Task.objects.filter(due_date__lt=today).exclude(status=Task.Status.DONE).count(),
                'delayed_projects': projects.filter(expected_completion__lt=today).exclude(
                    status__in=[Project.Status.COMPLETED, Project.Status.CANCELLED]
                ).count(),
            },
        }
    else:
        my_leads = Lead.objects.filter(Q(assigned_to=user) | Q(created_by=user))
        my_clients = Client.objects.filter(assigned_pm=user)
        my_projects = Project.objects.filter(assigned_pm=user)
        my_tasks = Task.objects.filter(assigned_to=user)
        my_followups = FollowUp.objects.filter(employee=user)
        from finance.models import Payment

        data = {
            'role': 'project_manager',
            'metrics': {
                'my_leads': my_leads.count(),
                'my_active_clients': my_clients.filter(status=Client.Status.ACTIVE).count(),
                'my_active_projects': my_projects.exclude(
                    status__in=[Project.Status.COMPLETED, Project.Status.CANCELLED]
                ).count(),
                'requirements_awaiting': Requirement.objects.filter(
                    created_by=user, status=Requirement.Status.AWAITING_APPROVAL
                ).count(),
                'requirements_approved': Requirement.objects.filter(
                    created_by=user, status=Requirement.Status.APPROVED
                ).count(),
                'tasks_due_today': my_tasks.filter(due_date=today).exclude(status=Task.Status.DONE).count(),
                'overdue_tasks': my_tasks.filter(due_date__lt=today).exclude(status=Task.Status.DONE).count(),
                'todays_followups': my_followups.filter(scheduled_at__date=today, status='scheduled').count(),
                'upcoming_followups': my_followups.filter(scheduled_at__gt=now, status='scheduled').count(),
                'pending_payments': Payment.objects.filter(
                    project__assigned_pm=user, status=Payment.Status.PENDING
                ).count(),
                'projects_near_delivery': my_projects.filter(
                    expected_completion__lte=today + timezone.timedelta(days=7)
                ).exclude(status__in=[Project.Status.COMPLETED, Project.Status.CANCELLED]).count(),
            },
        }
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_search(request):
    q = request.query_params.get('q', '').strip()
    if len(q) < 2:
        return Response({'results': []})
    user = request.user
    clients = Client.objects.filter(
        Q(client_name__icontains=q) | Q(company_name__icontains=q) | Q(phone__icontains=q) |
        Q(email__icontains=q) | Q(client_id__icontains=q)
    )
    projects = Project.objects.filter(Q(name__icontains=q) | Q(project_id__icontains=q))
    leads = Lead.objects.filter(Q(client_name__icontains=q) | Q(lead_id__icontains=q) | Q(phone__icontains=q))
    if not user.is_owner:
        clients = clients.filter(assigned_pm=user)
        projects = projects.filter(assigned_pm=user)
        leads = leads.filter(Q(assigned_to=user) | Q(created_by=user))
    return Response({
        'results': {
            'clients': ClientSerializer(clients[:10], many=True).data,
            'projects': ProjectListSerializer(projects[:10], many=True).data,
            'leads': LeadSerializer(leads[:10], many=True).data,
        }
    })
