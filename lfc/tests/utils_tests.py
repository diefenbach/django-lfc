# django imports
from django.test import TestCase

# lfc imports
import lfc.utils.registration
from lfc.models import BaseContent
from lfc.models import Page
from lfc.models import Portal
from lfc.tests.utils import create_request

class UtilsTestCase(TestCase):
    """
    """
    def setUp(self):
        Portal.objects.create()
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")
        self.p2 = Page.objects.create(title="Page 2", slug="page-2")

    def test_get_content_object(self):
        """
        """
        # As superuser
        ct = lfc.utils.get_content_object(slug="page-1")
        self.assertEqual(ct.title, "Page 1")

        request = create_request()
        request.user.is_superuser = False

        # Without passed request
        ct = lfc.utils.get_content_object(slug="page-1")
        self.assertEqual(ct.title, "Page 1")

        # With passed request
        ct = lfc.utils.get_content_object(request, slug="page-1")
        self.assertEqual(ct.title, "Page 1")

    def test_get_content_objects(self):
        """
        """
        # As superuser
        ct = lfc.utils.get_content_objects(slug="page-1")
        self.assertEqual(ct[0].title, "Page 1")

        request = create_request()
        request.user.is_superuser = False

        # Without passed request
        ct = lfc.utils.get_content_objects(slug="page-1")
        self.assertEqual(ct[0].title, "Page 1")

        # With passed request
        ct = lfc.utils.get_content_objects(request, slug="page-1")
        self.assertEqual(ct[0].title, "Page 1")