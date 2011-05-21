# django imports
from django.contrib.auth.models import AnonymousUser
from django.contrib.sitemaps import Sitemap

# lfc imports
from lfc.models import BaseContent


class PageSitemap(Sitemap):
    """Google's XML sitemap for pages.
    """
    changefreq = "daily"
    priority = 0.5

    def items(self):
        anon = AnonymousUser()
        objects = []
        for obj in BaseContent.objects.all():
            if obj.get_content_object().has_permission(anon, "view"):
                objects.append(obj)

        return objects

    def lastmod(self, obj):
        return obj.modification_date
