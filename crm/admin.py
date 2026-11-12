from django.contrib import admin
from crm.models import Client, FollowUp, Lead, Milestone, PendingWork, Project, ProjectMember, Requirement, Task


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('lead_id', 'client_name', 'phone', 'status', 'assigned_to', 'enquiry_date')
    list_filter = ('status', 'priority', 'lead_source')
    search_fields = ('lead_id', 'client_name', 'phone', 'email')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'client_name', 'company_name', 'phone', 'status', 'assigned_pm')
    search_fields = ('client_id', 'client_name', 'phone', 'email')


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ('requirement_id', 'client', 'status', 'estimated_value', 'version')
    list_filter = ('status',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_id', 'name', 'client', 'status', 'project_value', 'assigned_pm')
    list_filter = ('status', 'priority')


admin.site.register(ProjectMember)
admin.site.register(Milestone)
admin.site.register(Task)
admin.site.register(PendingWork)
admin.site.register(FollowUp)
