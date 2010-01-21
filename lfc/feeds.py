# django imports
from django.contrib.syndication.feeds import Feed
from django.core.exceptions import ObjectDoesNotExist

# tagging imports
from tagging.managers import ModelTaggedItemManager

# lfc imports
import lfc.utils
from lfc.models import BaseContent

class PageTagFeed(Feed):
    """Provides a feed for a given page and a given tag passed by the bits of an
    url.
    """
    def get_object(self, bits):
        if len(bits) not in (1, 2):
            raise ObjectDoesNotExist

        if len(bits) == 2:
            self.tag = bits[1]
        else:
            self.tag = None
        return BaseContent.objects.get(slug__exact=bits[0])

    def title(self, obj):
        portal = lfc.utils.get_portal()
        return "%s - %s" % (portal.title, obj.title)

    def link(self, obj):
        return obj.get_absolute_url()

    # def description(self, obj):
    #     return obj.description

    def items(self, obj):
        objs = obj.children.filter(active=True)
        if self.tag:
            objs = ModelTaggedItemManager().with_all(self.tag, objs)

        return objs