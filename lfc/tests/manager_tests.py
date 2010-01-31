# django imports
from django.test import TestCase

# lfc imports
from lfc.models import BaseContent
from lfc.models import Page
from lfc.tests.utils import create_request

class ManagerTestCase(TestCase):
    """
    """
    def setUp(self):
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")
        self.p2 = Page.objects.create(title="Page 2", slug="page-2")
        self.p2.active = True
        self.p2.save()

    def test_get(self):
        """
        """
        obj = BaseContent.objects.get(pk=1)
        self.failUnless(isinstance(obj, BaseContent))

    def test_get_content_object(self):
        """
        """
        obj = BaseContent.objects.get(pk=1).get_content_object()
        self.failUnless(isinstance(obj, Page))

    def test_get_content_objects(self):
        """
        """
        obj = BaseContent.objects.filter(pk=1).get_content_objects()
        self.failUnless(isinstance(obj[0], Page))

    def test_restricted_content_objects(self):
        """
        """
        request = create_request()
        pages = Page.objects.restricted(request)
        self.assertEqual(len(pages), 2)

        for page in pages:
            self.failUnless(isinstance(page, Page))

        request.user.is_superuser = False
        pages = Page.objects.restricted(request)
        self.assertEqual(pages[0].title, self.p2.title)

    def test_restricted(self):
        """
        """
        request = create_request()
        pages = Page.objects.restricted(request)
        self.assertEqual(len(pages), 2)

        request.user.is_superuser = False
        pages = Page.objects.restricted(request)
        self.assertEqual(pages[0].title, self.p2.title)