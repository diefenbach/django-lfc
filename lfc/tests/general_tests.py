# django imports
from django.test import TestCase
from django.utils import translation

# permissions imports
import permissions.utils

# lfc imports
from lfc.models import Page
from lfc.models import Portal
from lfc.tests.utils import create_request


class GeneralTestCase(TestCase):
    """Some general tests.
    """
    def setUp(self):
        """
        """
        from lfc.utils.initialize import initialize
        initialize(create_resources=False)

        self.p = Portal.objects.create()
        self.p.notification_emails = "john@doe.com, jane@doe.com"
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")

    def test_content_type(self):
        """
        """
        self.assertEqual(self.p.content_type, "portal")
        self.assertEqual(self.p.get_content_type(), "portal")

        self.assertEqual(self.p1.content_type, "page")
        self.assertEqual(self.p1.get_content_type(), "page")

