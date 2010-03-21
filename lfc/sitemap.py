# django imports
from django.contrib.sitemaps import Sitemap

# lfc imports
from lfc.models import Page

class PageSitemap(Sitemap):
    """Google's XML sitemap for pages.
    """
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Page.objects.filter(
            exclude_from_navigation=False,
        )

    def lastmod(self, obj):
        return obj.creation_date