# django imports
from django.conf import settings
from django.test import TestCase

# permissions imports
import permissions.utils

# lfc imports
import lfc.utils
from lfc.utils import import_module
from lfc.models import Application
from lfc.models import BaseContent
from lfc.models import Portal
from lfc.tests.utils import create_request

# lfc_page imports
from lfc_page.forms import PageDataForm
from lfc_page.models import Page

class PageTestCase(TestCase):
    """Tests for Page related stuff.
    """
    def setUp(self):
        """
        """
        from lfc.utils.initialize import initialize
        initialize()

        import_module("lfc_page").install()
        try:
            Application.objects.create(name="lfc_page")
        except Application.DoesNotExist:
            pass

        self.p = Portal.objects.create()
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")
        self.p11 = Page.objects.create(title="Page 1-1", slug="page-1-1", parent=self.p1)
        self.p111 = Page.objects.create(title="Page 1-1-1", slug="page-1-1-1", parent=self.p11)
        self.p12 = Page.objects.create(title="Page 1-2", slug="page-1-2", parent=self.p1)

        # for i18n tests
        self.p2en = Page.objects.create(title="Page 2 (en)", slug="page-2",
                                        language='en')
        self.p2de = Page.objects.create(title="Page 2 (de)", slug="page-2",
                                      language='de', canonical=self.p2en)
        self.p2fr = Page.objects.create(title="Page 2 (fr)", slug="page-2",
                                        language='fr', canonical=self.p2en)

        self.anonymous = permissions.utils.register_role("Anonymous")
        self.permission = permissions.utils.register_permission("View", "view")

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
        form = self.p1.edit_form()
        self.assertEqual(form.__class__, PageDataForm)

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
        # children = self.p1.get_children(request)
        # self.assertEqual(len(children), 2)
        #
        # # The cildren have to be specific objects
        # for child in children:
        #     self.failUnless(isinstance(child, Page))
        #
        # children = self.p1.get_children(request, slug="page-1-1")
        # self.assertEqual(len(children), 1)

        request.user.is_superuser = False

        # No page is active
        children = self.p1.get_children(request)
        self.assertEqual(len(children), 0)

        children = self.p1.get_children()
        self.assertEqual(len(children), 2)

        # Grant view permission to self.p11
        permissions.utils.grant_permission(self.p11, self.anonymous, "view")
        delattr(request.user, "permissions")

        result = self.p11.has_permission(request.user, "view")
        self.assertEqual(result, True)

        children = self.p1.get_children(request)
        self.assertEqual(len(children), 1)

        children = self.p1.get_children()
        self.assertEqual(len(children), 2)

        # Page 2 is not active
        children = self.p1.get_children(slug="page-1-2")
        self.assertEqual(len(children), 1)

        children = self.p1.get_children(request, slug="page-1-2")
        self.assertEqual(len(children), 0)

    # i18n tests
    def test_i18n_has_language(self):
        request = create_request()

        self.assertEqual(self.p2de.has_language(request, "de"), True)
        self.assertEqual(self.p2fr.has_language(request, "fr"), True)

        self.assertEqual(self.p2en.has_language(request, "en"), True)
        self.assertEqual(self.p2en.has_language(request, "de"), True)
        self.assertEqual(self.p2en.has_language(request, "fr"), True)
        self.assertEqual(self.p2en.has_language(request, "es"), False)

    def test_i18n_get_canonical(self):
        request = create_request()
        self.assertEqual(self.p2de.get_canonical(request), self.p2en)
        self.assertEqual(self.p2en.get_canonical(request), self.p2en)
        self.assertEqual(self.p2fr.get_canonical(request), self.p2en)

    def test_i18n_get_translation(self):
        request = create_request()
        self.assertEqual(self.p2en.is_translation(), False)
        self.assertEqual(self.p2de.is_translation(), True)
        self.assertEqual(self.p2fr.is_translation(), True)

    def test_i18n_get_translation2(self):
        request = create_request()
        translation = self.p2en.get_translation(request, 'en')
        if translation:
            self.assertEqual(translation, self.p2en)
        translation = self.p2en.get_translation(request, 'fr')
        if translation:
            self.assertEqual(translation, self.p2fr)
        translation = self.p2en.get_translation(request, 'de')
        if translation:
            self.assertEqual(translation, self.p2de)

    def test_i18n_get_translation3(self):
        request = create_request()
        translation = self.p2de.canonical.get_translation(request, 'en')
        if translation:
            self.assertEqual(translation, self.p2en)
        translation = self.p2fr.canonical.get_translation(request, 'en')
        if translation:
            self.assertEqual(translation, self.p2en)
        translation = self.p2fr.canonical.get_translation(request, 'de')
        if translation:
            self.assertEqual(translation, self.p2de)

    def test_i18n_view_set_language(self):
        request = create_request()
        from lfc.views import set_language

        self.assertEqual(set_language(request, 'de', self.p2en.id)['Location'],
                         '/de/page-2')
        self.assertEqual(set_language(request, 'fr', self.p2en.id)['Location'],
                         '/fr/page-2')

        self.assertEqual(set_language(request, 'fr', self.p2de.id)['Location'],
                         '/fr/page-2')
        self.assertEqual(set_language(request, 'en', self.p2en.id)['Location'],
                         '/page-2')
