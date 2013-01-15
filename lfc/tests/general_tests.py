# django imports
from django.test import TestCase
from django.utils import translation

# permissions imports
import permissions.utils

# lfc imports
from lfc.models import Application
from lfc.models import Portal
from lfc.tests.utils import create_request
from lfc.utils import import_module
from lfc.utils import delete_cache
from lfc.utils import get_cache
from lfc.utils import set_cache

# lfc_page imports
from lfc_page.models import Page


class GeneralTestCase(TestCase):
    """Some general tests.
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
        self.p.notification_emails = "john@doe.com, jane@doe.com"
        self.p1 = Page.objects.create(title="Page 1", slug="page-1")

    def test_content_type(self):
        """
        """
        self.assertEqual(self.p.content_type, u"portal")
        self.assertEqual(self.p.get_content_type(), u"Portal")

        self.assertEqual(self.p1.content_type, u"page")
        self.assertEqual(self.p1.get_content_type(), u"Page")

    def test_cache_1(self):
        """
        """
        self.assertRaises(AssertionError, set_cache, ["1"], "hurz_0")
        self.assertRaises(AssertionError, get_cache, ["1"])

        self.assertRaises(AssertionError, set_cache, "12", "hurz_0")

        # set_cache(["1", "2"], u"hurz_1")
        # temp = get_cache(["1", "2"])
        # self.assertEqual(temp, u"hurz_1")

        # delete_cache("1")
        # temp = get_cache(["1", "2"])
        # self.assertEqual(temp, None)

        set_cache(["A", "B", "C"], u"hurz_2")
        temp = get_cache(["A", "B", "C"])
        self.assertEqual(temp, u"hurz_2")

        set_cache(["1", "2", "3", "4"], u"hurz_3")
        set_cache(["1", "2", "3", "5"], u"hurz_4")
        temp = get_cache(["1", "2", "3", "4"])
        self.assertEqual(temp, u"hurz_3")

        temp = get_cache(["1", "2", "3", "5"])
        self.assertEqual(temp, u"hurz_4")

        temp = get_cache(["1", "2", "3"])
        self.assertEqual(temp, {'5': u'hurz_4', '4': u'hurz_3'})

    def test_cache_2(self):
        """
        """
        set_cache([1, "portlets", "left-slot"], u"portlets left")
        set_cache([1, "portlets", "right-slot"], u"portlets right")
        set_cache([1, "children"], ["c1", "c2"])

        self.assertEqual(get_cache(["1", "portlets", "left-slot"]), u"portlets left")
        self.assertEqual(get_cache(["1", "portlets", "right-slot"]), u"portlets right")
        self.assertEqual(get_cache(["1", "children"]), ["c1", "c2"])

        delete_cache("1")
        self.assertEqual(get_cache(["1", "portlets"]), None)
        self.assertEqual(get_cache(["1", "children"]), None)

    def test_cache_3(self):
        """
        """
        set_cache(["1", "2", "3", "4"], u"hurz_3")
        delete_cache(["1", "2", "3"])
        temp = get_cache(["1", "2"])
        self.assertEqual(temp, {})
