# django imports
from django.contrib.syndication.feeds import Feed
from django.core.exceptions import ObjectDoesNotExist

# tagging imports
from tagging.managers import ModelTaggedItemManager

# lfc imports
import lfc.utils
from lfc.models import BaseContent

class PageTagFeed(Feed):
    """Provides a feed for a given object restricted by given tags
    url, e.g.

    http://www.lfcproject.com/information/blog?tags=python
    """
    def get_object(self, bits):
        if len(bits) < 1:
            raise ObjectDoesNotExist

        return lfc.utils.traverse_object(self.request, "/".join(bits))

    def title(self, obj):
        portal = lfc.utils.get_portal()
        return "%s - %s" % (portal.title, obj.title)

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.description

    def items(self, obj):
        paths_objs = obj.get_descendants()

        tags = self.request.GET.getlist("tags")
        if not tags:
            return paths_objs
        else:
            objs = []
            tagged_objs = ModelTaggedItemManager().with_all(tags, BaseContent.objects.all())
            for obj in tagged_objs:
                if obj.get_content_object() in paths_objs:
                    objs.append(obj)
            return objs