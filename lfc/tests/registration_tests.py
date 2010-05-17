# django imports
from django.test import TestCase

# portlets imports
from portlets.models import PortletRegistration

# lfc imports
import lfc.utils.registration
from lfc.models import BaseContent
from lfc.models import Page
from lfc.models import Template
from lfc.models import ContentTypeRegistration

class RegistrationTestCase(TestCase):
    """Tests for registration related stuff.
    """
    def setUp(self):
        """
        """
        from lfc.utils.initialize import initialize
        initialize()

    def test_default_portlets(self):
        """Portlets which have to be registered at least.
        """
        portlets = ["Pages", "Random", "Text", "Navigation"]
        registered_portlets = [p.name for p in PortletRegistration.objects.all()]

        for portlet in portlets:
            self.failUnless(portlet in registered_portlets)

    def test_default_templates(self):
        """Templates which have to be registered.
        """
        templates = ["Plain", "Article", "Gallery", "Overview"]
        registered_templates = [t.name for t in Template.objects.all()]

        for template in templates:
            self.failUnless(template in registered_templates)

    def test_default_content_types(self):
        """ContentTypes which have to be registered by default.
        """
        content_types = ["Page"]
        registered_content_types = [ct.name for ct in ContentTypeRegistration.objects.all()]

        for content_type in content_types:
            self.failUnless(content_type in registered_content_types)

    def test_register_template(self):
        """Registering a new template.
        """
        lfc.utils.registration.register_template("New", "/path/to/nowhere.html", 23, 42)
        template = Template.objects.get(name="New")

    def test_register_content_type(self):
        """Registering a new content type.
        """
        class NewContent(BaseContent):
            pass

        lfc.utils.registration.register_content_type(
            NewContent, "New Content", sub_types=["Page"], templates=["Article"],
            default_template="Article")

        # by name
        info = lfc.utils.registration.get_info("newcontent")
        self.assertEqual(info.type, "newcontent")
        self.assertEqual(info.name, "New Content")
        self.assertEqual(info.display_select_standard, True)
        self.assertEqual(info.display_position, True)
        self.assertEqual(info.global_addable, True)
        self.assertEqual(info.subtypes.all()[0].name, "Page")
        self.assertEqual(info.templates.all()[0].name, "Article")
        self.assertEqual(info.default_template.name, "Article")

        # by object
        info = lfc.utils.registration.get_info(NewContent())
        self.assertEqual(info.type, "newcontent")
        self.assertEqual(info.type, "newcontent")
        self.assertEqual(info.name, "New Content")
        self.assertEqual(info.display_select_standard, True)
        self.assertEqual(info.display_position, True)
        self.assertEqual(info.global_addable, True)
        self.assertEqual(info.subtypes.all()[0].name, "Page")
        self.assertEqual(info.templates.all()[0].name, "Article")
        self.assertEqual(info.default_template.name, "Article")

    def test_unregister_content_type(self):
        """Unregistering a content type.
        """
        class NewContent(BaseContent):
            pass

        lfc.utils.registration.register_content_type(
            NewContent, "New Content", sub_types=["Page"], templates=["Article"],
            default_template="Article")

        info = lfc.utils.registration.get_info("newcontent")
        self.assertEqual(info.name, "New Content")

        lfc.utils.registration.unregister_content_type("New Content")
        info = lfc.utils.registration.get_info("newcontent")
        self.assertEqual(info, None)

    def test_register_sub_type(self):
        """
        """
        class NewContent(BaseContent):
            pass

        lfc.utils.registration.register_content_type(
            NewContent, "New Content", sub_types=["Page"], templates=["Article"],
            default_template="Article")

        lfc.utils.registration.register_sub_type(NewContent, "Page")

        new_info = lfc.utils.registration.get_info("newcontent")
        page_info = lfc.utils.registration.get_info("page")
        self.failUnless(new_info in page_info.subtypes.all())

        self.failUnless(new_info in lfc.utils.registration.get_allowed_subtypes(Page()))
