# django imports
from django.contrib.auth.models import User
from django.contrib.sessions.backends.file import SessionStore
from django.core.management import call_command
from django.test import TestCase

# lfc imports
from lfc.manage.views import do_transition
from lfc.manage.views import lfc_copy
from lfc.models import History
from lfc.tests.utils import RequestFactory

# lfc_page imports
from lfc_page.models import Page


class HistoryTestCase(TestCase):
    """
    Tests related to the object history.
    """
    def setUp(self):
        self.user = User.objects.create(username="admin", is_active=True, is_superuser=True)
        call_command('lfc_init_simple')

        self.p1 = Page.objects.create(title="Page 1", slug="page-1")

    def test_change_workflow_state(self):
        """
        For each change a history object should be created.
        """
        request = RequestFactory().get("/", {"transition": 1})
        request.user = self.user
        request.session = SessionStore()

        do_transition(request, self.p1.id)
        self.assertEqual(History.objects.count(), 1)

        do_transition(request, self.p1.id)
        self.assertEqual(History.objects.count(), 2)

        # Delete content object
        self.p1.delete()

        self.assertEqual(History.objects.count(), 0)

    def test_copy(self):
        """
        Tests the history after an object has been copied.
        """
        request = RequestFactory().get("/", {"transition": 1})
        request.user = self.user
        request.session = SessionStore()

        do_transition(request, self.p1.id)
        self.assertEqual(History.objects.count(), 1)

        lfc_copy(request, self.p1.id)

        self.assertEqual(History.objects.count(), 1)
