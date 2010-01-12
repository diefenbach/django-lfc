# django imports
from django.contrib.auth.models import User
from django.contrib.sessions.backends.file import SessionStore
from django.core.urlresolvers import reverse
from django.template.loader import get_template_from_string
from django.template import Context
from django.test import TestCase
from django.test.client import Client

from lfc.models import Page

class LFCViewsTestCase(TestCase):
    """
    """
    def setUp(self):
        """
        """
        self.p = Page.objects.create(title="Page 1", slug="page-1")

    def test_page_defaults(self):
        self.assertEqual(self.p.title, "Page 1")
        self.assertEqual(self.p.slug, "page-1")
        
        self.assertEqual(self.p.meta_keywords, "<tags>")
        self.assertEqual(self.p.meta_description, "<description>")