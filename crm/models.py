from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Lead(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        CONTACTED = 'contacted', 'Contacted'
        DISCUSSION = 'discussion', 'Discussion'
        REQUIREMENT_COLLECTED = 'requirement_collected', 'Requirement Collected'
        PROPOSAL_SENT = 'proposal_sent', 'Proposal Sent'
        NEGOTIATION = 'negotiation', 'Negotiation'
        CONFIRMED = 'confirmed', 'Confirmed'
        LOST = 'lost', 'Lost'
        ON_HOLD = 'on_hold', 'On Hold'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    lead_id = models.CharField(max_length=20, unique=True, blank=True)
    client_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    business_type = models.CharField(max_length=100, blank=True)
    required_service = models.CharField(max_length=255, blank=True)
    lead_source = models.CharField(max_length=100, blank=True)
    enquiry_date = models.DateField(default=timezone.localdate)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads'
    )
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    client_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    notes = models.TextField(blank=True)
    next_follow_up = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.NEW)
    converted_client = models.ForeignKey(
        'Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_leads'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_leads'
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.lead_id:
            last = Lead.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.lead_id = f'LD{n:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.lead_id} – {self.client_name}'


class Client(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ON_HOLD = 'on_hold', 'On Hold'
        ARCHIVED = 'archived', 'Archived'

    client_id = models.CharField(max_length=20, unique=True, blank=True)
    client_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    business_type = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    gst_details = models.CharField(max_length=50, blank=True)
    lead_source = models.CharField(max_length=100, blank=True)
    assigned_pm = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_clients'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_clients'
    )

    class Meta:
        ordering = ['client_name']

    def save(self, *args, **kwargs):
        if not self.client_id:
            last = Client.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.client_id = f'CL{n:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.client_id} – {self.client_name}'


class Requirement(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        AWAITING_APPROVAL = 'awaiting_approval', 'Awaiting Owner Approval'
        CHANGES_REQUESTED = 'changes_requested', 'Changes Requested'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SUPERSEDED = 'superseded', 'Superseded'

    requirement_id = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='requirements')
    company = models.CharField(max_length=255, blank=True)
    business_objective = models.TextField(blank=True)
    current_problem = models.TextField(blank=True)
    solution_type = models.CharField(max_length=100, blank=True)
    required_platforms = models.CharField(max_length=255, blank=True)
    user_types = models.TextField(blank=True)
    customer_features = models.TextField(blank=True)
    staff_features = models.TextField(blank=True)
    admin_features = models.TextField(blank=True)
    detailed_features = models.TextField(blank=True)
    essential_features = models.TextField(blank=True)
    future_features = models.TextField(blank=True)
    integrations = models.TextField(blank=True)
    payment_requirements = models.TextField(blank=True)
    notifications = models.TextField(blank=True)
    location_gps = models.TextField(blank=True)
    reference_apps = models.TextField(blank=True)
    expected_timeline = models.CharField(max_length=255, blank=True)
    client_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    meeting_notes = models.TextField(blank=True)
    clarification_questions = models.TextField(blank=True)
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.DRAFT)
    version = models.PositiveIntegerField(default=1)
    parent_requirement = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='revisions'
    )
    owner_comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requirements'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_requirements'
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.requirement_id:
            last = Requirement.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.requirement_id = f'RQ{n:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.requirement_id} v{self.version} – {self.client}'


class Project(TimeStampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        PLANNING = 'planning', 'Planning'
        UIUX = 'uiux', 'UI/UX Design'
        DESIGN_APPROVAL = 'design_approval', 'Design Approval'
        DEVELOPMENT = 'development', 'Development'
        INTERNAL_TESTING = 'internal_testing', 'Internal Testing'
        CLIENT_REVIEW = 'client_review', 'Client Review'
        REVISIONS = 'revisions', 'Revisions'
        READY_FOR_LAUNCH = 'ready_for_launch', 'Ready for Launch'
        COMPLETED = 'completed', 'Completed'
        ON_HOLD = 'on_hold', 'On Hold'
        CANCELLED = 'cancelled', 'Cancelled'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    project_id = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    requirement = models.ForeignKey(
        Requirement, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects'
    )
    name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=100, blank=True)
    approved_scope = models.TextField(blank=True)
    project_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_schedule = models.TextField(blank=True)
    assigned_pm = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects'
    )
    start_date = models.DateField(null=True, blank=True)
    expected_completion = models.DateField(null=True, blank=True)
    actual_completion = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.NOT_STARTED)
    blockers = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_projects'
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.project_id:
            last = Project.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.project_id = f'PR{n:05d}'
        super().save(*args, **kwargs)

    @property
    def total_verified_payments(self):
        from finance.models import Payment
        total = (
            self.payments.filter(status=Payment.Status.VERIFIED)
            .aggregate(s=models.Sum('amount'))['s']
            or 0
        )
        return total

    @property
    def outstanding_balance(self):
        return self.project_value - self.total_verified_payments

    def __str__(self):
        return f'{self.project_id} – {self.name}'


class ProjectMember(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships')
    role_label = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('project', 'user')


class Milestone(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        DELAYED = 'delayed', 'Delayed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'due_date']


class Task(TimeStampedModel):
    class Status(models.TextChoices):
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        REVIEW = 'review', 'Review'
        DONE = 'done', 'Done'
        BLOCKED = 'blocked', 'Blocked'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    task_id = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks'
    )
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    completion_date = models.DateField(null=True, blank=True)
    comments = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_tasks'
    )

    class Meta:
        ordering = ['due_date', '-priority']

    def save(self, *args, **kwargs):
        if not self.task_id:
            last = Task.objects.order_by('-id').first()
            n = (last.id + 1) if last else 1
            self.task_id = f'TK{n:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.task_id} – {self.title}'


class PendingWork(TimeStampedModel):
    class Category(models.TextChoices):
        CLIENT = 'client', 'Pending from Client'
        DEVELOPER = 'developer', 'Pending from Developer'
        INTERNAL = 'internal', 'Pending Internally'
        OWNER_APPROVAL = 'owner_approval', 'Pending Owner Approval'
        COMPLETED = 'completed', 'Completed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='pending_items', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pending_items', null=True, blank=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.CLIENT)
    description = models.TextField()
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pending_responsibilities'
    )
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    latest_update = models.TextField(blank=True)
    next_action = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_pending'
    )

    class Meta:
        ordering = ['due_date', '-priority']


class FollowUp(TimeStampedModel):
    class Method(models.TextChoices):
        CALL = 'call', 'Call'
        EMAIL = 'email', 'Email'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        MEETING = 'meeting', 'Meeting'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        MISSED = 'missed', 'Missed'
        CANCELLED = 'cancelled', 'Cancelled'

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='followups', null=True, blank=True)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='followups', null=True, blank=True)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='followups'
    )
    scheduled_at = models.DateTimeField()
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CALL)
    discussion_notes = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    next_action = models.TextField(blank=True)
    next_follow_up = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    class Meta:
        ordering = ['scheduled_at']
