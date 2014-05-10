# django imports
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase
from django.test.client import Client

# permissions imports
from permissions.models import PrincipalRoleRelation
from permissions.models import Role
import permissions.utils

# workflows imports
from workflows.models import Transition

# portlets imports
from portlets.models import Portlet
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot

# lfc imports
import lfc.utils.registration
from lfc.models import Portal
from lfc.tests.utils import create_request

# lfc_page imports
from lfc_page.models import Page


class InheritancePermissionTestCase(TestCase):
    """
    """
    fixtures = ["superuser.xml"]


class LFCPermissionTestCase2(TestCase):
    """
    """
    fixtures = ["superuser.xml"]

    def setUp(self):
        """
        """
        Portal.objects.create()
        self.editor = Role.objects.create(name="editor")
        self.user = User.objects.create(username="user", is_active=True)
        self.user.set_password("secret")
        self.user.save()

        self.group = Group.objects.create(name="group")

        self.page_1 = Page.objects.create(title="Page 1", slug="page-1")
        self.page_2 = Page.objects.create(title="Page 2", slug="page-2", parent=self.page_1)
        self.page_3 = Page.objects.create(title="Page 3", slug="page-3", parent=self.page_2)

    def test_delete_user(self):
        """
        """
        request = create_request()

        roles = PrincipalRoleRelation.objects.all()
        self.assertEqual(len(roles), 0)

        permissions.utils.add_local_role(self.page_1, self.user, self.editor)

        roles = PrincipalRoleRelation.objects.all()
        self.assertEqual(len(roles), 1)

        from lfc.manage.views import delete_user
        delete_user(request, self.user.id)

        roles = PrincipalRoleRelation.objects.all()
        self.assertEqual(len(roles), 0)

    def test_delete_group(self):
        """
        """
        request = create_request()

        roles = PrincipalRoleRelation.objects.all()
        self.assertEqual(len(roles), 0)

        permissions.utils.add_local_role(self.page_1, self.group, self.editor)

        roles = PrincipalRoleRelation.objects.all()
        self.assertEqual(len(roles), 1)

        from lfc.manage.views import delete_group
        delete_group(request, self.group.id)

        roles = PrincipalRoleRelation.objects.all()
        self.assertEqual(len(roles), 0)

    def test_local_roles_from_parent_1(self):
        """
        """
        permissions.utils.add_local_role(self.page_1, self.user, self.editor)

        roles = permissions.utils.get_roles(self.user, self.page_1)
        self.assertEqual(list(roles), [self.editor])

        roles = permissions.utils.get_roles(self.user, self.page_2)
        self.assertEqual(list(roles), [self.editor])

        roles = permissions.utils.get_roles(self.user, self.page_3)
        self.assertEqual(list(roles), [self.editor])

    def test_local_roles_from_parent_2(self):
        """
        """
        permissions.utils.add_local_role(self.page_2, self.user, self.editor)

        roles = permissions.utils.get_roles(self.user, self.page_1)
        self.assertEqual(list(roles), [])

        roles = permissions.utils.get_roles(self.user, self.page_2)
        self.assertEqual(list(roles), [self.editor])

        roles = permissions.utils.get_roles(self.user, self.page_3)
        self.assertEqual(list(roles), [self.editor])

    def test_local_roles_from_parent_3(self):
        """
        """
        permissions.utils.add_local_role(self.page_3, self.user, self.editor)

        roles = permissions.utils.get_roles(self.user, self.page_1)
        self.assertEqual(list(roles), [])

        roles = permissions.utils.get_roles(self.user, self.page_2)
        self.assertEqual(list(roles), [])

        roles = permissions.utils.get_roles(self.user, self.page_3)
        self.assertEqual(list(roles), [self.editor])

    def test_local_roles_from_group_1(self):
        """
        """
        # Add user to group
        self.user.groups.add(self.group)

        # Assign "editor" to group on page 3
        permissions.utils.add_local_role(self.page_1, self.group, self.editor)

        roles = permissions.utils.get_roles(self.user, self.page_1)
        self.assertEqual(list(roles), [self.editor])

        roles = permissions.utils.get_roles(self.user, self.page_2)
        self.assertEqual(list(roles), [self.editor])

        roles = permissions.utils.get_roles(self.user, self.page_3)
        self.assertEqual(list(roles), [self.editor])

    def test_local_roles_from_group_2(self):
        """
        """
        # Add user to group
        self.user.groups.add(self.group)

        # Assign "editor" to group on page 2
        permissions.utils.add_local_role(self.page_2, self.group, self.editor)

        roles = permissions.utils.get_roles(self.user, self.page_1)
        self.assertEqual(list(roles), [])

        roles = permissions.utils.get_roles(self.user, self.page_2)
        self.assertEqual(list(roles), [self.editor])

        roles = permissions.utils.get_roles(self.user, self.page_3)
        self.assertEqual(list(roles), [self.editor])

    def test_local_roles_from_group_3(self):
        """
        """
        # Add user to group
        self.user.groups.add(self.group)

        # Assign "editor" to group on page 3
        permissions.utils.add_local_role(self.page_3, self.group, self.editor)

        roles = permissions.utils.get_roles(self.user, self.page_1)
        self.assertEqual(list(roles), [])

        roles = permissions.utils.get_roles(self.user, self.page_2)
        self.assertEqual(list(roles), [])

        roles = permissions.utils.get_roles(self.user, self.page_3)
        self.assertEqual(list(roles), [self.editor])

    def test_local_roles_from_group_4(self):
        """
        """
        # Add user to group
        self.user.groups.add(self.group)

        # Assign "editor" to group on page 2 and 3
        permissions.utils.add_local_role(self.page_3, self.group, self.editor)
        permissions.utils.add_local_role(self.page_2, self.group, self.editor)

        roles = permissions.utils.get_roles(self.user, self.page_1)
        self.assertEqual(list(roles), [])

        roles = permissions.utils.get_roles(self.user, self.page_2)
        self.assertEqual(list(roles), [self.editor])

        roles = permissions.utils.get_roles(self.user, self.page_3)
        self.assertEqual(list(roles), [self.editor])


class LFCPermissionTestCase(TestCase):
    """
    """
    fixtures = ["superuser.xml"]

    def setUp(self):
        # Initialize LFC
        from lfc.management.commands.lfc_init import Command
        Command().handle()

        # Create a slot
        self.left_slot = Slot.objects.create(name="Left")

        # Create a page
        self.page = Page.objects.filter()[0]
        self.ctype = ContentType.objects.get_for_model(self.page)

        self.portal = lfc.utils.get_portal()
        self.portal_ctype = ContentType.objects.get_for_model(self.portal)

    def test_reviewer(self):
        """Tests access rights of a reviewer.
        """
        reviewer = User.objects.create(username="reviewer", is_active=True)
        reviewer.set_password("reviewer")
        reviewer.save()

        role = Role.objects.get(name="Reviewer")
        role.add_principal(reviewer)

        self.assertEqual(role.get_users(), [reviewer])

        self.client = Client()

        result = self.client.login(username="reviewer", password="reviewer")
        self.assertEqual(result, True)

        # Page is public, so anonymous should be able to view that page
        result = self.client.get(reverse("lfc_base_view", kwargs={"slug": "welcome-to-lfc"}))
        self.failIf(result.content.find("Welcome to LFC") == -1)

        result = self.client.get(reverse("lfc_manage_users"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # portal
        result = self.client.post(reverse("lfc_save_portal_core"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # applications
        result = self.client.get(reverse("lfc_applications"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_install_application", kwargs={"name": "dummy"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_uninstall_application", kwargs={"name": "dummy"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_reinstall_application", kwargs={"name": "dummy"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # content types
        result = self.client.get(reverse("lfc_content_types"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_content_type", kwargs={"id": 0}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # manage content
        # page is public so the review can view it within the manage screens.
        result = self.client.get(reverse("lfc_manage_object", kwargs={"id": self.page.id}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(reverse("lfc_add_object", kwargs={"id": 0}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_add_top_object"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_add_object", kwargs={"id": 0, "language": "en"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_delete_object", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_save_object_core_data", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_save_meta_data", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_save_seo", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # object images
        result = self.client.post(reverse("lfc_add_images", kwargs={"id": self.page.id}), {"sessionid": self.client.session.session_key})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_update_images", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_load_object_images", kwargs={"id": self.page.id}))
        self.failIf(result.content.find("images") == -1)

        # portal images
        result = self.client.post(reverse("lfc_add_portal_images"), {"sessionid": self.client.session.session_key})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_update_portal_images"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_load_portal_images"))
        self.assertEqual(result.status_code, 200)

        # object files
        result = self.client.post(reverse("lfc_add_files", kwargs={"id": self.page.id}), {"sessionid": self.client.session.session_key})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_update_files", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_load_object_files", kwargs={"id": self.page.id}))
        self.failIf(result.content.find("files") == -1)

        # portal files
        result = self.client.post(reverse("lfc_add_portal_files"), {"sessionid": self.client.session.session_key})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_update_portal_files"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_load_portal_files"))
        self.assertEqual(result.status_code, 200)

        # comments
        result = self.client.get(reverse("lfc_update_comments", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # children
        result = self.client.get(reverse("lfc_update_object_children", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_update_portal_children"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # permissions
        result = self.client.get(reverse("lfc_update_object_permissions", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_update_portal_permissions"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # workflows
        transition = Transition.objects.get(name="Reject", workflow__name="Portal")
        result = self.client.get(reverse("lfc_manage_do_transition", kwargs={"id": self.page.id}) + "?transition=" + str(transition.id))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(reverse("lfc_manage_workflow", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_workflow"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_workflow"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_workflow", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_state", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_transition", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_workflow_data", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_workflow_state", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_workflow_state", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_workflow_state", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_workflow_transition", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_workflow_transition", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_workflow_transition", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # object portlets
        from lfc_portlets.models import ContentPortlet
        self.portlet = ContentPortlet()
        self.portlet.id = 1

        # Assign the portlet to th page
        self.pa = PortletAssignment.objects.create(
            slot=self.left_slot, content=self.page, portlet=self.portlet, position=1)

        result = self.client.get(reverse("lfc_add_portlet", kwargs={"object_type_id": self.ctype.id, "object_id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_update_portlets_blocking", kwargs={"object_type_id": self.ctype.id, "object_id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_delete_portlet", kwargs={"portletassignment_id": self.pa.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_edit_portlet", kwargs={"portletassignment_id": self.pa.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # portal portlets
        # Assign the portlet to th page
        self.pa = PortletAssignment.objects.create(
            slot=self.left_slot, content=self.portal, portlet=self.portlet, position=1)

        result = self.client.get(reverse("lfc_add_portlet", kwargs={"object_type_id": self.portal_ctype.id, "object_id": self.portal.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_update_portlets_blocking", kwargs={"object_type_id": self.portal_ctype.id, "object_id": self.portal.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_delete_portlet", kwargs={"portletassignment_id": self.pa.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_edit_portlet", kwargs={"portletassignment_id": self.pa.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # review
        result = self.client.get(reverse("lfc_manage_review"))
        self.failIf(result.content.find("There are no objects to review") == -1)

        # local roles
        result = self.client.get(reverse("lfc_manage_save_local_roles", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_local_roles_add_form", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_local_roles_search", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_local_roles", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # translation
        result = self.client.post(reverse("lfc_save_translation"), {"canonical_id": self.page.id})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_translate_object", kwargs={"id": self.page.id, "language": "en"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # language
        # Note: All logged in user are allowed to change the language
        result = self.client.get(reverse("lfc_set_navigation_tree_language", kwargs={"language": "en"}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(reverse("lfc_manage_set_language", kwargs={"language": "en"}), HTTP_REFERER =  "/")
        self.failIf(result._headers["location"][1].startswith("http://testserver/login"))

        # template
        result = self.client.post(reverse("lfc_set_template"), {"obj_id": self.page.id})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # users
        result = self.client.get(reverse("lfc_manage_users"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_user", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_user"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_save_user_data", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_add_user"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_delete_user", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_change_users"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_change_password", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_users_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_reset_users_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_users_page"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_users_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_reset_users_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_reset_user_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_user_page"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # groups
        result = self.client.get(reverse("lfc_manage_group"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_group", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_group"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_group", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_group", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # roles
        result = self.client.get(reverse("lfc_manage_role"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_role", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_role"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_role", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_role", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # portal
        result = self.client.get(reverse("lfc_manage_portal"))
        self.assertEqual(result.status_code, 200)

    def test_anonymous(self):
        """Tests access rights of an anonymous user.
        """
        self.client = Client()
        result = self.client.logout()

        # Page is public, so anonymous should be able to view that page
        result = self.client.get(reverse("lfc_base_view", kwargs={"slug": "welcome-to-lfc"}))
        self.failIf(result.content.find("Welcome to LFC") == -1)

        result = self.client.get(reverse("lfc_manage_users"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # portal
        result = self.client.post(reverse("lfc_save_portal_core"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # applications
        result = self.client.get(reverse("lfc_applications"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_install_application", kwargs={"name": "dummy"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_uninstall_application", kwargs={"name": "dummy"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_reinstall_application", kwargs={"name": "dummy"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # content types
        result = self.client.get(reverse("lfc_content_types"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_content_type", kwargs={"id": 0}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # manage content
        result = self.client.get(reverse("lfc_manage_object", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_add_object", kwargs={"id": 0}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_add_top_object"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_add_object", kwargs={"id": 0, "language": "en"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_delete_object", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_save_object_core_data", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_save_meta_data", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_save_seo", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # object images
        result = self.client.post(reverse("lfc_add_images", kwargs={"id": self.page.id}), {"sessionid": "dummy"})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_update_images", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_load_object_images", kwargs={"id": self.page.id}))
        self.failIf(result.content.find("images") == -1)

        # portal images
        result = self.client.post(reverse("lfc_add_portal_images"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_update_portal_images"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_load_portal_images"))
        self.failUnless(result.status_code, 200)

        # object files
        result = self.client.post(reverse("lfc_add_files", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_update_files", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_load_object_files", kwargs={"id": self.page.id}))
        self.failIf(result.content.find("files") == -1)

        # portal files
        result = self.client.post(reverse("lfc_add_portal_files"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.post(reverse("lfc_update_portal_files"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_load_portal_files"))
        self.failUnless(result.status_code, 200)

        # comments
        result = self.client.get(reverse("lfc_update_comments", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # children
        result = self.client.get(reverse("lfc_update_object_children", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_update_portal_children"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # permissions
        result = self.client.get(reverse("lfc_update_object_permissions", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_update_portal_permissions"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # workflows
        transition = Transition.objects.get(name="Reject", workflow__name="Portal")
        result = self.client.get(reverse("lfc_manage_do_transition", kwargs={"id": self.page.id}) + "?transition=" + str(transition.id))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_workflow", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_workflow"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_workflow"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_workflow", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_state", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_transition", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_workflow_data", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_workflow_state", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_workflow_state", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_workflow_state", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_workflow_transition", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_workflow_transition", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_workflow_transition", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # object portlets
        from lfc_portlets.models import ContentPortlet
        self.portlet = ContentPortlet()
        self.portlet.id = 1

        # Assign the portlet to th page
        self.pa = PortletAssignment.objects.create(
            slot=self.left_slot, content=self.page, portlet=self.portlet, position=1)

        result = self.client.get(reverse("lfc_add_portlet", kwargs={"object_type_id": self.ctype.id, "object_id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_update_portlets_blocking", kwargs={"object_type_id": self.ctype.id, "object_id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_delete_portlet", kwargs={"portletassignment_id": self.pa.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_edit_portlet", kwargs={"portletassignment_id": self.pa.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # portal portlets
        # Assign the portlet to th page
        self.pa = PortletAssignment.objects.create(
            slot=self.left_slot, content=self.portal, portlet=self.portlet, position=1)

        result = self.client.get(reverse("lfc_add_portlet", kwargs={"object_type_id": self.portal_ctype.id, "object_id": self.portal.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_update_portlets_blocking", kwargs={"object_type_id": self.portal_ctype.id, "object_id": self.portal.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_delete_portlet", kwargs={"portletassignment_id": self.pa.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_edit_portlet", kwargs={"portletassignment_id": self.pa.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # reviewe
        result = self.client.get(reverse("lfc_manage_review"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # local roles
        result = self.client.get(reverse("lfc_manage_save_local_roles", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_local_roles_add_form", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_local_roles_search", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_local_roles", kwargs={"id": self.page.id}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # translation
        result = self.client.post(reverse("lfc_save_translation"), {"canonical_id": self.page.id})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_translate_object", kwargs={"id": self.page.id, "language": "en"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # language
        result = self.client.get(reverse("lfc_set_navigation_tree_language", kwargs={"language": "en"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_language", kwargs={"language": "en"}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # template
        result = self.client.post(reverse("lfc_set_template"), {"obj_id": self.page.id})
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # users
        result = self.client.get(reverse("lfc_manage_users"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_user", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_user"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_save_user_data", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_add_user"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_delete_user", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_change_users"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_change_password", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_users_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_reset_users_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_users_page"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_users_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_reset_users_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_reset_user_filter"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_set_user_page"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # groups
        result = self.client.get(reverse("lfc_manage_group"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_group", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_group"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_group", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_group", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # roles
        result = self.client.get(reverse("lfc_manage_role"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_role", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_add_role"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_save_role", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        result = self.client.get(reverse("lfc_manage_delete_role", kwargs={"id": 1}))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))

        # portal
        result = self.client.get(reverse("lfc_manage_portal"))
        self.failUnless(result._headers["location"][1].startswith("http://testserver/login"))
