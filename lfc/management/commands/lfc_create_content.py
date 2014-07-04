# django imports
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = ''
    help = """Creates test content"""

    def handle(self, *args, **options):
        from lfc_page.models import Page

        p = Page.objects.create(title="Page-1", slug="page-1")

        for i in range(1, 100):
            Page.objects.create(title="Page-%s" % i, slug="page-%s" % i, parent=p)
