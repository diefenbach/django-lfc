# django imports
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# permissions imports
import permissions.utils

# lfc imports
from lfc.models import Role


class Command(BaseCommand):
    args = ''
    help = """Creates test users for roles: author, editor, manager, reviewer"""

    def handle(self, *args, **options):
        User.objects.exclude(username="admin").delete()

        author = User.objects.create(username="author", is_active=True)
        permissions.utils.add_role(author, Role.objects.get(name="Author"))

        editor = User.objects.create(username="editor", is_active=True)
        permissions.utils.add_role(editor, Role.objects.get(name="Editor"))

        manager = User.objects.create(username="manager", is_active=True)
        permissions.utils.add_role(manager, Role.objects.get(name="Manager"))

        reviewer = User.objects.create(username="reviewer", is_active=True)
        permissions.utils.add_role(reviewer, Role.objects.get(name="Reviewer"))

        for user in User.objects.exclude(username="admin"):
            user.set_password("1")
            user.save()
