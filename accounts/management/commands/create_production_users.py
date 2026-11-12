from django.core.management.base import BaseCommand, CommandError
from accounts.models import User


class Command(BaseCommand):
    help = 'Create/update production Super Admin and Staff users'

    def add_arguments(self, parser):
        parser.add_argument('--admin-username', default='admin')
        parser.add_argument('--admin-email', default='admin@digitechavenue.com')
        parser.add_argument('--admin-password', required=True)
        parser.add_argument('--staff-username', default='staff')
        parser.add_argument('--staff-email', default='staff@digitechavenue.com')
        parser.add_argument('--staff-password', required=True)

    def handle(self, *args, **options):
        admin_password = options['admin_password']
        staff_password = options['staff_password']
        if len(admin_password) < 10 or len(staff_password) < 10:
            raise CommandError('Passwords must be at least 10 characters.')

        admin, _ = User.objects.update_or_create(
            username=options['admin_username'],
            defaults={
                'email': options['admin_email'],
                'first_name': 'Digitech',
                'last_name': 'Admin',
                'role': User.Role.OWNER,
                'designation': 'Super Admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_active_employee': True,
            },
        )
        admin.set_password(admin_password)
        admin.role = User.Role.OWNER
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        staff, _ = User.objects.update_or_create(
            username=options['staff_username'],
            defaults={
                'email': options['staff_email'],
                'first_name': 'Digitech',
                'last_name': 'Staff',
                'role': User.Role.PROJECT_MANAGER,
                'designation': 'Project Manager',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'is_active_employee': True,
            },
        )
        staff.set_password(staff_password)
        staff.role = User.Role.PROJECT_MANAGER
        staff.is_superuser = False
        staff.save()

        self.stdout.write(self.style.SUCCESS('Production users ready:'))
        self.stdout.write(f"  Super Admin: {admin.username} ({admin.email})")
        self.stdout.write(f"  Staff:       {staff.username} ({staff.email})")
