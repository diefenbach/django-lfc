# django imports
from django.core.management.base import BaseCommand

from lfc.management.commands.utils import create_extended_permissions
class Command(BaseCommand):
    args = ''
    help = """Creates extended permissions:

        * Manage Applications
        * Manage Groups
        * Manage Reviews
        * Manage Roles
        * Manage Users
        * Manage Workflows
    """

    def handle(self, *args, **options):
        create_extended_permissions()
