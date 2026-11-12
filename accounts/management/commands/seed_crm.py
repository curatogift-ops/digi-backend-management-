from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from crm.models import Client, FollowUp, Lead, Milestone, PendingWork, Project, Requirement, Task
from finance.models import Expense, Invoice, Payment


class Command(BaseCommand):
    help = 'Seed Digitech Avenue CRM with demo Owner, PM, and sample data'

    def handle(self, *args, **options):
        owner, created = User.objects.get_or_create(
            username='owner',
            defaults={
                'email': 'owner@digitechavenue.com',
                'first_name': 'Adnan',
                'last_name': 'Shaikh',
                'role': User.Role.OWNER,
                'phone': '9000000001',
                'designation': 'Owner',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created or not owner.has_usable_password():
            owner.set_password('Owner@123')
            owner.save()
        else:
            owner.role = User.Role.OWNER
            owner.set_password('Owner@123')
            owner.save()

        pm, created = User.objects.get_or_create(
            username='pm',
            defaults={
                'email': 'pm@digitechavenue.com',
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'role': User.Role.PROJECT_MANAGER,
                'phone': '9000000002',
                'designation': 'Project Manager',
            },
        )
        pm.set_password('PM@12345')
        pm.role = User.Role.PROJECT_MANAGER
        pm.save()

        dev, _ = User.objects.get_or_create(
            username='dev',
            defaults={
                'email': 'dev@digitechavenue.com',
                'first_name': 'Rahul',
                'last_name': 'Patel',
                'role': User.Role.DEVELOPER,
                'phone': '9000000003',
                'designation': 'Developer',
            },
        )
        dev.set_password('Dev@12345')
        dev.save()

        if Lead.objects.exists():
            self.stdout.write(self.style.WARNING('Sample data already exists. Users refreshed.'))
            self._print_credentials()
            return

        today = timezone.now().date()
        now = timezone.now()

        lead1 = Lead.objects.create(
            client_name='Apex Retail',
            company='Apex Retail Pvt Ltd',
            contact_person='Suresh Mehta',
            phone='9876500001',
            email='suresh@apexretail.com',
            location='Mumbai',
            business_type='Retail',
            required_service='E-commerce App',
            lead_source='Website',
            enquiry_date=today - timedelta(days=5),
            assigned_to=pm,
            estimated_value=Decimal('350000'),
            client_budget=Decimal('300000'),
            priority=Lead.Priority.HIGH,
            notes='Interested in Android + iOS shopping app',
            next_follow_up=now + timedelta(days=1),
            status=Lead.Status.DISCUSSION,
            created_by=pm,
        )
        Lead.objects.create(
            client_name='GreenFarm Co',
            company='GreenFarm',
            contact_person='Anita Desai',
            phone='9876500002',
            email='anita@greenfarm.in',
            location='Pune',
            required_service='CRM Website',
            lead_source='Referral',
            enquiry_date=today - timedelta(days=2),
            assigned_to=pm,
            estimated_value=Decimal('120000'),
            priority=Lead.Priority.MEDIUM,
            status=Lead.Status.NEW,
            created_by=pm,
        )

        client = Client.objects.create(
            client_name='Nova Hospitals',
            company_name='Nova Hospitals Group',
            contact_person='Dr. Kavita Rao',
            phone='9876500010',
            email='it@novahospitals.com',
            address='Bandra West, Mumbai',
            location='Mumbai',
            industry='Healthcare',
            business_type='Hospital',
            website='https://novahospitals.example.com',
            gst_details='27AAAAA0000A1Z5',
            lead_source='LinkedIn',
            assigned_pm=pm,
            status=Client.Status.ACTIVE,
            notes='Long-term client for patient portal',
            created_by=owner,
        )
        lead1.status = Lead.Status.CONFIRMED
        lead1.converted_client = client
        lead1.save()

        req = Requirement.objects.create(
            client=client,
            company=client.company_name,
            business_objective='Digitise patient appointments and reports',
            current_problem='Manual appointment booking and paper reports',
            solution_type='Web + Mobile App',
            required_platforms='Web, Android, iOS',
            user_types='Patients, Doctors, Admin staff',
            customer_features='Book appointment, view reports, pay bills',
            staff_features='Manage slots, upload reports',
            admin_features='User management, analytics dashboard',
            detailed_features='OTP login, PDF reports, UPI payments',
            essential_features='Appointments, reports, payments',
            future_features='Teleconsultation, pharmacy',
            integrations='Razorpay, SMS gateway',
            expected_timeline='12 weeks',
            client_budget=Decimal('500000'),
            estimated_value=Decimal('550000'),
            meeting_notes='Kickoff call completed',
            status=Requirement.Status.APPROVED,
            submitted_at=now - timedelta(days=10),
            reviewed_at=now - timedelta(days=8),
            reviewed_by=owner,
            created_by=pm,
        )

        project = Project.objects.create(
            client=client,
            requirement=req,
            name='Nova Patient Portal',
            service_type='Web + Mobile App',
            approved_scope=req.essential_features,
            project_value=Decimal('550000'),
            advance_amount=Decimal('150000'),
            payment_schedule='40% advance, 30% mid, 30% delivery',
            assigned_pm=pm,
            start_date=today - timedelta(days=20),
            expected_completion=today + timedelta(days=40),
            priority=Project.Priority.HIGH,
            status=Project.Status.DEVELOPMENT,
            created_by=owner,
        )
        project.members.create(user=pm, role_label='Project Manager')
        project.members.create(user=dev, role_label='Full-stack Developer')

        Milestone.objects.create(project=project, title='UI/UX Approval', status='completed', order=1, due_date=today - timedelta(days=10))
        Milestone.objects.create(project=project, title='Backend APIs', status='in_progress', order=2, due_date=today + timedelta(days=7))
        Milestone.objects.create(project=project, title='Client UAT', status='pending', order=3, due_date=today + timedelta(days=30))

        Task.objects.create(
            client=client, project=project, title='Build appointment booking API',
            description='CRUD + slot availability', assigned_to=dev,
            priority=Task.Priority.HIGH, due_date=today + timedelta(days=3),
            status=Task.Status.IN_PROGRESS, created_by=pm,
        )
        Task.objects.create(
            client=client, project=project, title='Prepare UAT checklist',
            assigned_to=pm, priority=Task.Priority.MEDIUM, due_date=today,
            status=Task.Status.TODO, created_by=pm,
        )

        PendingWork.objects.create(
            client=client, project=project, category=PendingWork.Category.CLIENT,
            description='Need logo assets and brand colours', responsible=pm,
            due_date=today + timedelta(days=2), priority=PendingWork.Priority.HIGH,
            next_action='Call client for assets', created_by=pm,
        )

        FollowUp.objects.create(
            client=client, project=project, employee=pm,
            scheduled_at=now.replace(hour=11, minute=0, second=0, microsecond=0),
            method=FollowUp.Method.CALL, discussion_notes='', status=FollowUp.Status.SCHEDULED,
        )
        FollowUp.objects.create(
            lead=Lead.objects.filter(status=Lead.Status.NEW).first(), employee=pm,
            scheduled_at=now + timedelta(days=1), method=FollowUp.Method.WHATSAPP,
            status=FollowUp.Status.SCHEDULED,
        )

        Payment.objects.create(
            client=client, project=project, amount=Decimal('150000'),
            payment_date=today - timedelta(days=18), method=Payment.Method.BANK_TRANSFER,
            transaction_reference='NEFT882211', collection_notes='Advance payment',
            status=Payment.Status.VERIFIED, submitted_by=pm, verified_by=owner,
            verified_at=now - timedelta(days=17),
        )
        Payment.objects.create(
            client=client, project=project, amount=Decimal('100000'),
            payment_date=today - timedelta(days=1), method=Payment.Method.UPI,
            transaction_reference='UPI998877', collection_notes='Second instalment',
            status=Payment.Status.PENDING, submitted_by=pm,
        )

        Expense.objects.create(
            title='AWS hosting – March', category='Infrastructure', amount=Decimal('8500'),
            expense_date=today - timedelta(days=3), project=project, status='approved',
            submitted_by=pm, reviewed_by=owner,
        )
        Invoice.objects.create(
            client=client, project=project, invoice_date=today - timedelta(days=18),
            due_date=today + timedelta(days=12), taxable_amount=Decimal('150000'),
            tax_amount=Decimal('27000'), total_amount=Decimal('177000'),
            paid_amount=Decimal('150000'), status=Invoice.Status.PARTIALLY_PAID, created_by=owner,
        )

        Requirement.objects.create(
            client=client, company=client.company_name,
            business_objective='Pharmacy module addition',
            solution_type='Module Extension', estimated_value=Decimal('80000'),
            status=Requirement.Status.AWAITING_APPROVAL, submitted_at=now - timedelta(hours=5),
            created_by=pm, essential_features='Inventory, billing, prescriptions',
        )

        self.stdout.write(self.style.SUCCESS('CRM seeded successfully.'))
        self._print_credentials()

    def _print_credentials(self):
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('  Owner:  owner / Owner@123')
        self.stdout.write('  PM:     pm / PM@12345')
        self.stdout.write('  Dev:    dev / Dev@12345')
