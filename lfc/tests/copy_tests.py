# django imports
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

# lfc imports
import lfc.utils.registration
from lfc.models import Page
from lfc.models import Portal

class CopyTestCase(TestCase):
    """
    """
    fixtures = ["superuser.xml"]

    def setUp(self):
        from lfc.utils.initialize import initialize
        initialize()

        Portal.objects.create(id=1)
        self.p1 = Page.objects.create(id=1, title="Page 1", slug="page-1")
        self.p11 = Page.objects.create(id=11, title="Page 1-1", slug="page-1-1", parent = self.p1)
        self.p2 = Page.objects.create(id=2, title="Page 2", slug="page-2")
        
        self.client = Client()
        self.client.login(username="admin", password="admin")
        
    def test_cut(self):
        """Tests general cut and paste of objects.
        """
        # P1 has no parent
        p1 = lfc.utils.get_content_object(pk=1)
        self.assertEqual(self.p1.parent, None)

        # Cut
        self.client.get(reverse("lfc_cut", kwargs={"id" : 1}))

        # Paste
        result = self.client.get(reverse("lfc_paste", kwargs={"id" : 2}))

        # P1 has now p2 as parent
        p1 = lfc.utils.get_content_object(pk=1)
        self.assertEqual(p1.parent.id, 2)

        # Portal has only p2 as child
        portal = lfc.utils.get_portal()
        self.assertEqual(len(portal.get_children()), 1)
        self.assertEqual(portal.get_children()[0].id, 2)

    def test_copy(self):
        """Tests general copy and paste of objects.
        """
        p1 = lfc.utils.get_content_object(pk=1)
        self.assertEqual(self.p1.parent, None)

        # Copy
        self.client.get(reverse("lfc_copy", kwargs={"id" : 1}))

        # Paste
        self.client.get(reverse("lfc_paste", kwargs={"id" : 2}))

        # p2 has now a child
        self.assertEqual(len(self.p2.children.all()), 1)
        self.assertEqual(self.p2.children.all()[0].title, "Page 1")

        # Paste again
        result = self.client.get(reverse("lfc_paste", kwargs={"id" : 2}))

        # p2 has now a two children
        self.assertEqual(len(self.p2.children.all()), 2)
        self.assertEqual(self.p2.children.all()[0].slug, "page-1")
        self.assertEqual(self.p2.children.all()[1].slug, "page-1-1")

        # The portal has still both objects
        portal = lfc.utils.get_portal()
        self.assertEqual(len(portal.get_children()), 2)
        self.assertEqual(portal.get_children()[0].id, 1)
        self.assertEqual(portal.get_children()[1].id, 2)

    def test_paste_dissallowed_type(self):
        """Tests to copy and paste an dissallowed content type.
        """
        ctr = lfc.utils.registration.get_info("page")
        ctr.subtypes = []
        ctr.save()

        # Cut
        self.client.get(reverse("lfc_cut", kwargs={"id" : 1}))

        # Paste
        self.client.get(reverse("lfc_paste", kwargs={"id" : 2}))

        # p2 has no children
        self.assertEqual(len(self.p2.children.all()), 0)

        # Cut
        self.client.get(reverse("lfc_cut", kwargs={"id" : 1}))

        # Paste
        self.client.get(reverse("lfc_paste", kwargs={"id" : 2}))

        # p2 has no children
        self.assertEqual(len(self.p2.children.all()), 0)

    def test_cut_and_paste_to_itself(self):
        """Cut and paste to itself is dissallowed.
        """
        # Cut
        self.client.get(reverse("lfc_cut", kwargs={"id" : 2}))

        # Paste to itself
        self.client.get(reverse("lfc_paste", kwargs={"id" : 2}))

        # P2 has children
        self.assertEqual(len(self.p2.children.all()), 0)

    def test_cut_and_paste_to_descendant(self):
        """Cut and paste to descendant is dissallowed.
        """
        # Cut
        self.client.get(reverse("lfc_cut", kwargs={"id" : 1}))

        # Paste to descendant
        self.client.get(reverse("lfc_paste", kwargs={"id" : 11}))

        # Portal has still 2 children
        portal = lfc.utils.get_portal()
        self.assertEqual(len(portal.get_children()), 2)

        # P1 has still one children
        self.assertEqual(len(self.p1.get_children()), 1)

    def test_copy_and_paste_to_itself(self):
        """Copy and paste to itself is disallowed.
        """
        # Copy
        self.client.get(reverse("lfc_copy", kwargs={"id" : 2}))

        # Paste to itself is allowed
        self.client.get(reverse("lfc_paste", kwargs={"id" : 2}))

        # P2 has children
        self.assertEqual(len(self.p2.children.all()), 1)

    def test_copy_and_paste_to_descendant(self):
        """Cut and paste to descendant is dissallowed.
        """
        # Cut
        self.client.get(reverse("lfc_copy", kwargs={"id" : 1}))

        # Paste to descendant
        self.client.get(reverse("lfc_paste", kwargs={"id" : 11}))

        # Portal has still 2 children
        portal = lfc.utils.get_portal()
        self.assertEqual(len(portal.get_children()), 2)

        # P1 has still one children
        self.assertEqual(len(self.p1.get_children()), 1)

    # def test_copy_with_tags(self):
    #     """
    #     """
    #     client = Client()
    #
    #     self.p1.tags.add("dog")
    #