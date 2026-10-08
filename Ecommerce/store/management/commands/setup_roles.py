"""
Management command that creates staff groups and assigns their permissions.

Run it after `migrate` on any new environment:

    python manage.py setup_roles

It is safe to run multiple times: groups are reused, and each group's
permissions are reset to exactly match the ROLES definition below.
"""


from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


# Staff roles mapped to the permission codenames each role is granted.
# Customers need no group, and admins are superusers.

ROLES = {
    'Product Managers' : ['view_category','add_category','change_category',
                          'view_product','add_product',
                          'change_product','delete_product',
                          'view_productimage','add_productimage',
                          'change_productimage','delete_productimage'
                          ],
}


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        for role, codenames in ROLES.items():
            group , _ = Group.objects.get_or_create(name = role)
            permissions = Permission.objects.filter(codename__in = codenames)
            group.permissions.set(permissions)

            # Warn about codenames that do not exist (typos, renamed or missing models)
            found = permissions.values_list('codename',flat=True)

            if missing:=set(codenames) - set(found):
                self.stdout.write(
                    self.style.WARNING(
                        f'{role} : missing permissions {sorted(missing)}'
                        ))

            self.stdout.write(
                self.style.SUCCESS(
                    f'{role} : {permissions.count()} permissions assigned '
                    ))

