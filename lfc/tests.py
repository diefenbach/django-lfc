# python 
import copy

# django imports
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.backends.file import SessionStore
from django.core.handlers.wsgi import WSGIRequest
from django.core.urlresolvers import reverse
from django.template.loader import get_template_from_string
from django.template import Context
from django.test import TestCase
from django.test.client import Client

# portlets imports
from portlets.utils import get_registered_portlets
from portlets.models import PortletRegistration

# lfc imports
import lfc.utils.registration
from lfc.manage.forms import CoreDataForm
from lfc.models import BaseContent
from lfc.models import Page
from lfc.models import Portal
from lfc.models import Template
from lfc.models import ContentTypeRegistration

# Taken from "http://www.djangosnippets.org/snippets/963/"
class RequestFactory(Client):
    """
    Class that lets you create mock Request objects for use in testing.

    Usage:

    rf = RequestFactory()
    get_request = rf.get('/hello/')
    post_request = rf.post('/submit/', {'foo': 'bar'})

    This class re-uses the django.test.client.Client interface, docs here:
    http://www.djangoproject.com/documentation/testing/#the-test-client

    Once you have a request object you can pass it to any view function,
    just as if that view had been hooked up using a URLconf.

    """
    def request(self, **request):
        """
        Similar to parent class, but returns the request object as soon as it
        has created it.
        """
        environ = {
            'HTTP_COOKIE': self.cookies,
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'SERVER_PROTOCOL': 'HTTP/1.1',
        }
        environ.update(self.defaults)
        environ.update(request)
        return WSGIRequest(environ)

def create_request():
    """
    """
    rf = RequestFactory()
    request = rf.get('/')
    request.session = SessionStore()

    user = User()
    user.is_superuser = True
    user.save()
    request.user = user

    return request

class CopyTestCase(TestCase):
    """
    """
    def setUp(self):
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")
        self.p2 = Page.objects.create(title="Page 2", slug="page-2")

    def test_copy(self):
        """
        """
        page_copy = copy.deepcopy(self.p1)
        page_copy.id = None
        page_copy.pk = None        
        page_copy.parent = self.p2
        page_copy.save()

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
        self.failUnless(isinstance(obj, Page))

    def test_restricted_content_objects(self):
        """
        """
        request = create_request()
        pages = BaseContent.objects.restricted(request).content_objects()
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

class RegistrationTestCase(TestCase):
    """Tests for registration related stuff.
    """
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

class PortalTestCase(TestCase):
    """Some tests for the Portal class.
    """
    def setUp(self):
        """
        """
        self.p = Portal.objects.create()
        self.p.notification_emails = "john@doe.com, jane@doe.com"
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")
        self.p11 = Page.objects.create(title="Page 1-1", slug="page-1-1", parent=self.p1)
        self.p111 = Page.objects.create(title="Page 1-1-1", slug="page-1-1-1", parent=self.p11)
        self.p12 = Page.objects.create(title="Page 1-2", slug="page-1-2", parent=self.p1)
        self.p12 = Page.objects.create(title="Page 2", slug="page-2")
    
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

        # Only page 1 is active
        self.p1.active = True
        self.p1.save()

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

class PageTestCase(TestCase):
    """Tests for Page related stuff.
    """
    def setUp(self):
        """
        """
        self.p = Portal.objects.create()
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")
        self.p11 = Page.objects.create(title="Page 1-1", slug="page-1-1", parent=self.p1)
        self.p111 = Page.objects.create(title="Page 1-1-1", slug="page-1-1-1", parent=self.p11)
        self.p12 = Page.objects.create(title="Page 1-2", slug="page-1-2", parent=self.p1)

    def test_page_defaults(self):
        """Tests the default values of a freshly added page.
        """
        self.assertEqual(self.p1.title, "Page 1")
        self.assertEqual(self.p1.slug, "page-1")
        self.assertEqual(self.p1.display_title, True)
        self.assertEqual(self.p1.position, 1)
        self.assertEqual(self.p1.language, "0")
        self.assertEqual(self.p1.canonical, None)
        self.assertEqual(self.p1.tags, "")
        self.assertEqual(self.p1.parent, None)
        self.assertEqual(self.p1.template, None)
        self.assertEqual(self.p1.standard, None)
        self.assertEqual(self.p1.active, False)
        self.assertEqual(self.p1.exclude_from_navigation, False)
        self.assertEqual(self.p1.exclude_from_search, False)
        self.assertEqual(self.p1.creator, None)
        self.assertEqual(len(self.p1.images.all()), 0)
        self.assertEqual(self.p1.allow_comments, 1)
        self.assertEqual(self.p1.searchable_text, "Page 1")

        self.assertEqual(self.p1.meta_keywords, "<tags>")
        self.assertEqual(self.p1.meta_description, "<description>")

        self.assertEqual(self.p1.content_type, "page")

    def test_get_absolute_url(self):
        """
        """
        self.p1.language = settings.LANGUAGE_CODE
        self.p1.save()

        url = self.p1.get_absolute_url()
        self.assertEqual(url, "/page-1")

        self.p11.language = settings.LANGUAGE_CODE
        self.p11.save()

        url = self.p11.get_absolute_url()
        self.assertEqual(url, "/page-1/page-1-1")

    def test_get_content_object(self):
        """
        """
        bc = BaseContent.objects.get(slug="page-1")
        ct = bc.get_content_object()

        self.assertEqual(ct, self.p1)

    def test_get_searchable_text(self):
        """
        """
        self.assertEqual(self.p1.get_searchable_text(), "Page 1")

    def test_get_form(self):
        """
        """
        form = self.p1.form()
        self.assertEqual(form.__class__, CoreDataForm)

    def test_get_ancestors(self):
        """
        """
        self.assertEqual(self.p1.get_ancestors(), [])
        self.assertEqual(self.p11.get_ancestors(), [self.p1])
        self.assertEqual(self.p111.get_ancestors(), [self.p11, self.p1])
        self.assertEqual(self.p111.get_ancestors_reverse(), [self.p1, self.p11])

    def test_get_image(self):
        """
        """
        self.assertEqual(self.p1.get_image(), None)

    def test_get_meta_keywords(self):
        """
        """
        self.assertEqual(self.p1.get_meta_keywords(), "")

        self.p1.tags = "Dog, Cat"
        self.assertEqual(self.p1.get_meta_keywords(), "Dog, Cat")

        self.p1.meta_keywords = "<title>"
        self.assertEqual(self.p1.get_meta_keywords(), "Page 1")

        self.p1.meta_keywords = "<description>"
        self.p1.description = "Description"
        self.assertEqual(self.p1.get_meta_keywords(), "Description")

        self.p1.meta_keywords = "<tags>, <title>, <description>"
        self.assertEqual(self.p1.get_meta_keywords(), "Dog, Cat, Page 1, Description")

    def test_get_meta_description(self):
        """
        """
        self.p1.description = "Description"
        self.assertEqual(self.p1.get_meta_description(), "Description")

        self.p1.tags = "Dog, Cat"
        self.p1.meta_description = "<tags>"
        self.assertEqual(self.p1.get_meta_description(), "Dog, Cat")

        self.p1.meta_description = "<title>"
        self.assertEqual(self.p1.get_meta_description(), "Page 1")

        self.p1.meta_description = "<tags>, <title>, <description>"
        self.assertEqual(self.p1.get_meta_description(), "Dog, Cat, Page 1, Description")

    def test_get_template(self):
        """
        """
        self.assertEqual(self.p1.get_template().name, "Article")

    def test_get_title(self):
        """
        """
        self.assertEqual(self.p1.get_title(), "Page 1")

        self.p1.display_title = False
        self.assertEqual(self.p1.get_title(), "")

    def test_is_canonical(self):
        """
        """
        self.assertEqual(self.p1.is_canonical(), True)

    def test_get_canonical(self):
        """
        """
        request = create_request()
        self.assertEqual(self.p1.get_canonical(request), self.p1)

    def test_is_translation(self):
        """
        """
        self.assertEqual(self.p1.is_translation(), False)

    def test_has_language(self):
        """
        """
        request = create_request()
        # Returns True if the object is neutral
        self.assertEqual(self.p1.has_language(request, "en-us"), True)
        self.assertEqual(self.p1.has_language(request, "de"), True)

        self.p1.language = "en-us"
        self.assertEqual(self.p1.has_language(request, "en-us"), True)
        self.assertEqual(self.p1.has_language(request, "de"), False)

    def test_get_translation(self):
        """
        """
        request = create_request()
        self.assertEqual(self.p1.get_translation(request, "en-us"), None)

    def test_are_comments_allowed(self):
        """
        """
        self.assertEqual(self.p1.are_comments_allowed(), False)

    def test_get_descendants(self):
        """
        """
        descendants = self.p1.get_descendants()
        self.assertEqual(len(descendants), 3)

        self.failUnless(self.p11 in descendants)
        self.failUnless(self.p111 in descendants)
        self.failUnless(self.p12 in descendants)

        descendants = self.p11.get_descendants()
        self.assertEqual(len(descendants), 1)
        self.failUnless(self.p111 in descendants)

    def test_get_children(self):
        """
        """
        request = create_request()
        children = self.p1.get_children(request)
        self.assertEqual(len(children), 2)

        # The cildren have to be specific objects
        for child in children:
            self.failUnless(isinstance(child, Page))

        children = self.p1.get_children(request, slug="page-1-1")
        self.assertEqual(len(children), 1)

        request.user.is_superuser = False

        # No page is active
        children = self.p1.get_children(request)
        self.assertEqual(len(children), 0)

        children = self.p1.get_children()
        self.assertEqual(len(children), 2)

        # Only page 1 is active
        self.p11.active = True
        self.p11.save()

        children = self.p1.get_children(request)
        self.assertEqual(len(children), 1)

        children = self.p1.get_children()
        self.assertEqual(len(children), 2)

        # Page 2 is not active
        children = self.p1.get_children(slug="page-1-2")
        self.assertEqual(len(children), 1)

        children = self.p1.get_children(request, slug="page-1-2")
        self.assertEqual(len(children), 0)