# django imports
from django.test import TestCase

# permissions imports
import permissions.utils

# lfc imports
from lfc.models import BaseContent
from lfc.models import Page
from lfc.models import Portal
from lfc.tests.utils import create_request

class ManagerTestCase(TestCase):
    """
    """
    def setUp(self):
        """
        """
        Portal.objects.create()
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")
        self.p2 = Page.objects.create(title="Page 2", slug="page-2")

        self.anonymous = permissions.utils.register_role("Anonymous")
        self.permission = permissions.utils.register_permission("View", "view")

        permissions.utils.grant_permission(self.p2, self.anonymous, "view")

    def test_get(self):
        """
        """
        obj = BaseContent.objects.get(slug="page-1")
        self.failUnless(isinstance(obj, BaseContent))

    def test_get_content_object(self):
        """
        """
        obj = BaseContent.objects.get(slug="page-1").get_content_object()
        self.failUnless(isinstance(obj, Page))

    def test_get_content_objects(self):
        """
        """
        obj = BaseContent.objects.filter(slug="page-1").get_content_objects()
        self.failUnless(isinstance(obj[0], Page))