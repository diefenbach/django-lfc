# django imports
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = ''
    help = """Initializes LFC"""

    def handle(self, *args, **options):
        from lfc.models import Page
        p = Page.objects.create(title="Hurz", slug="hurz")
        
        p.text = "Hurz"
        p.save()
