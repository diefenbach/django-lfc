# django imports
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test.client import Client

# lfc imports
import lfc.manage.views
import lfc.utils.registration
from lfc.models import BaseContent
from lfc.models import NavigationPortlet
from lfc.models import Page
from lfc.models import Portal
from lfc.models import TextPortlet
from lfc.tests.utils import create_request

# portlets imports
from portlets.models import PortletAssignment
from portlets.models import Slot

class PortletsTestCase(TestCase):
    """
    """
    fixtures = ["superuser.xml"]
    
    def setUp(self):
        """
        """
        # Initialize LFC
        from lfc.management.commands.lfc_init import Command
        Command().handle()
        
        self.page = Page.objects.create(title="Page 1", slug="page-1")
        self.request = create_request()
        self.client = Client()
        self.client.login(username="admin", password="admin")

    def test_delete_portlet(self):
        """
        """
        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 0)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 0)

        ctype = ContentType.objects.get_for_model(self.page)        
        self.client.post(reverse("lfc_add_portlet", kwargs={"object_type_id" : ctype.id, "object_id" : self.page.id}), {"portlet_type" : "navigationportlet", "portlet-start_level" : 1, "portlet-expand_level" : 1, "slot" : 1, "position" : 1})

        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 1)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 1)
        
        self.client.post(reverse("lfc_delete_portlet", kwargs={"portletassignment_id" : pas[0].id}))

        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 0)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 0)
        
        ss = Slot.objects.all()
        self.assertEqual(len(ss), 2)        
        
    def test_delete_portlet_2(self):
        """Two portlets of a kind.
        """
        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 0)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 0)

        ctype = ContentType.objects.get_for_model(self.page)        
        self.client.post(reverse("lfc_add_portlet", kwargs={"object_type_id" : ctype.id, "object_id" : self.page.id}), {"portlet_type" : "navigationportlet", "portlet-start_level" : 1, "portlet-expand_level" : 1, "slot" : 1, "position" : 1})

        ctype = ContentType.objects.get_for_model(self.page)        
        self.client.post(reverse("lfc_add_portlet", kwargs={"object_type_id" : ctype.id, "object_id" : self.page.id}), {"portlet_type" : "navigationportlet", "portlet-start_level" : 1, "portlet-expand_level" : 1, "slot" : 1, "position" : 2})

        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 2)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 2)
        
        self.client.post(reverse("lfc_delete_portlet", kwargs={"portletassignment_id" : pas[0].id}))

        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 1)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 1)

        ss = Slot.objects.all()
        self.assertEqual(len(ss), 2)        
        
    def test_delete_portlet_3(self):
        """Two portlets of different kind.
        """
        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 0)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 0)

        ctype = ContentType.objects.get_for_model(self.page)
        self.client.post(reverse("lfc_add_portlet", kwargs={"object_type_id" : ctype.id, "object_id" : self.page.id}), {"portlet_type" : "navigationportlet", "portlet-start_level" : 1, "portlet-expand_level" : 1, "slot" : 1, "position" : 1})

        ctype = ContentType.objects.get_for_model(self.page)        
        self.client.post(reverse("lfc_add_portlet", kwargs={"object_type_id" : ctype.id, "object_id" : self.page.id}), {"portlet_type" : "textportlet", "slot" : 1, "position" : 2})

        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 2)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 1)

        ps = TextPortlet.objects.all()
        self.assertEqual(len(ps), 1)
        
        self.client.post(reverse("lfc_delete_portlet", kwargs={"portletassignment_id" : pas[0].id}))

        pas = PortletAssignment.objects.all()
        self.assertEqual(len(pas), 1)

        ps = NavigationPortlet.objects.all()
        self.assertEqual(len(ps), 0)        

        ps = TextPortlet.objects.all()
        self.assertEqual(len(ps), 1)

        ss = Slot.objects.all()
        self.assertEqual(len(ss), 2)        
        