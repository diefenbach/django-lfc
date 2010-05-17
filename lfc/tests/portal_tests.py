# django imports
from django.test import TestCase

# permissions imports
import permissions.utils

# lfc imports
from lfc.models import Page
from lfc.models import Portal
from lfc.tests.utils import create_request

class PortalTestCase(TestCase):
    """Some tests for the Portal class.
    """
    def setUp(self):
        """
        """
        from lfc.utils.initialize import initialize
        initialize()

        self.p = Portal.objects.create()
        self.p.notification_emails = "john@doe.com, jane@doe.com"
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")
        self.p11 = Page.objects.create(title="Page 1-1", slug="page-1-1", parent=self.p1)
        self.p111 = Page.objects.create(title="Page 1-1-1", slug="page-1-1-1", parent=self.p11)
        self.p12 = Page.objects.create(title="Page 1-2", slug="page-1-2", parent=self.p1)
        self.p12 = Page.objects.create(title="Page 2", slug="page-2")

        self.anonymous = permissions.utils.register_role("Anonymous")
        self.permission = permissions.utils.register_permission("View", "view")

    def test_get_children(self):
        """
        """
        request = create_request()
        children = self.p.get_children(request)
        self.assertEqual(len(children), 2)

        # The cildren have to be specific objects
        for child in children:
            self.failUnless(isinstance(child, Page))

        children = self.p.get_children(request, slug="page-2")
        self.assertEqual(len(children), 1)

        request.user.is_superuser = False

        # No page is active
        children = self.p.get_children(request)
        self.assertEqual(len(children), 0)

        children = self.p.get_children()
        self.assertEqual(len(children), 2)

        permissions.utils.grant_permission(self.p1, self.anonymous, "view")
        children = self.p.get_children(request)
        self.assertEqual(len(children), 1)

        children = self.p.get_children()
        self.assertEqual(len(children), 2)

        # Page 2 is not active
        children = self.p.get_children(slug="page-2")
        self.assertEqual(len(children), 1)

        children = self.p.get_children(request, slug="page-2")
        self.assertEqual(len(children), 0)

    def test_get_parent_for_portlets(self):
        """
        """
        self.assertEqual(self.p.get_parent_for_portlets(), None)

    def test_are_comments_allowed(self):
        """
        """
        self.assertEqual(self.p.are_comments_allowed(), False)

        self.p.allow_comments = True
        self.p.save()
        self.assertEqual(self.p.are_comments_allowed(), True)

    def test_get_template(self):
        """
        """
        self.assertEqual(self.p.get_template().name, "Article")

    def test_get_notification_emails(self):
        """
        """
        self.assertEqual(self.p.get_notification_emails(), ["john@doe.com", "jane@doe.com"])

