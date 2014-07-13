# django imports
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

# lfc imports
from lfc.manage.views import checkin
from lfc.manage.views import checkout
from lfc.tests.utils import create_request

# lfc_page imports
from lfc_page.models import Page


class WorkingCopyTestCase(TestCase):
    """
    Tests related to working copy.
    """
    def setUp(self):
        self.user = User.objects.create(username="admin", is_active=True, is_superuser=True)
        call_command('lfc_init_simple')

        self.p1 = Page.objects.create(title="Page 1", slug="page-1")

    def test_working_cycle(self):
        request = create_request()

        self.assertEqual(Page.objects.count(), 2)
        checkout(request, self.p1.id)

        self.assertEqual(Page.objects.count(), 3)
        self.assertTrue(self.p1.has_working_copy())
        self.assertFalse(self.p1.is_working_copy())

        wc = self.p1.get_working_copy()
        self.assertFalse(wc.has_working_copy())
        self.assertTrue(wc.is_working_copy())

        checkin(request, wc.id)
        self.assertEqual(Page.objects.count(), 2)
