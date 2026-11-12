from rest_framework import serializers
from crm.models import (
    Client, FollowUp, Lead, Milestone, PendingWork, Project, ProjectMember, Requirement, Task,
)


class LeadSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.display_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['lead_id', 'created_by', 'created_at', 'updated_at']


class ClientSerializer(serializers.ModelSerializer):
    assigned_pm_name = serializers.CharField(source='assigned_pm.display_name', read_only=True, default='')
    project_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['client_id', 'created_by', 'created_at', 'updated_at']

    def get_project_count(self, obj):
        return obj.projects.count()


class ClientDetailSerializer(ClientSerializer):
    projects = serializers.SerializerMethodField()

    def get_projects(self, obj):
        return ProjectListSerializer(obj.projects.all(), many=True).data


class RequirementSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True, default='')

    class Meta:
        model = Requirement
        fields = '__all__'
        read_only_fields = [
            'requirement_id', 'created_by', 'submitted_at', 'reviewed_at',
            'reviewed_by', 'created_at', 'updated_at',
        ]


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.display_name', read_only=True)

    class Meta:
        model = ProjectMember
        fields = '__all__'


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'


class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    assigned_pm_name = serializers.CharField(source='assigned_pm.display_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_verified_payments = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    outstanding_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'project_id', 'client', 'client_name', 'name', 'service_type',
            'project_value', 'advance_amount', 'assigned_pm', 'assigned_pm_name',
            'start_date', 'expected_completion', 'priority', 'status', 'status_display',
            'total_verified_payments', 'outstanding_balance', 'created_at',
        ]


class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    assigned_pm_name = serializers.CharField(source='assigned_pm.display_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_verified_payments = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    outstanding_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['project_id', 'created_by', 'created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.display_name', read_only=True, default='')
    project_name = serializers.CharField(source='project.name', read_only=True, default='')
    client_name = serializers.CharField(source='client.client_name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['task_id', 'created_by', 'created_at', 'updated_at']


class PendingWorkSerializer(serializers.ModelSerializer):
    responsible_name = serializers.CharField(source='responsible.display_name', read_only=True, default='')
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = PendingWork
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class FollowUpSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.display_name', read_only=True, default='')
    client_name = serializers.CharField(source='client.client_name', read_only=True, default='')
    lead_name = serializers.CharField(source='lead.client_name', read_only=True, default='')

    class Meta:
        model = FollowUp
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
