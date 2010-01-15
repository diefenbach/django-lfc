# python imports
import datetime
import urllib

# django settings
from django.conf import settings
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import _get_queryset
from django.utils import simplejson
from django.utils.functional import Promise
from django.utils.encoding import force_unicode
from django.utils import translation

# lfc imports
import lfc.models

def get_current_pages(page):
    """
    """
    pages = [page]
    pages.extend(page.get_ancestors())

def get_portal(pk=1):
    """Returns the default portal, which should always exist and have id=1.
    """
    try:
        return lfc.models.Portal.objects.get(pk=pk)
    except lfc.models.Portal.DoesNotExist:
        return lfc.models.Portal.objects.filter()[0]

def getLOL(objects, objects_per_row=3):
    """Returns a list of list of given objects.
    """
    result = []
    row = []
    for i, object in enumerate(objects):
        row.append(object)
        if (i+1) % objects_per_row == 0:
            result.append(row)
            row = []

    if len(row) > 0:
        result.append(row)

    return result

class LazyEncoder(simplejson.JSONEncoder):
    """Encodes django's lazy i18n strings.
    """
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return obj

def lfc_quote(string, encoding="utf-8"):
    """Encodes string to encoding before quoting.
    """
    return urllib.quote(string.encode(encoding))

def set_message_cookie(url, msg):
    """Creates response object with given url and adds message cookie with passed
    message.
    """
    # We just keep the message two seconds.
    max_age = 2
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() +
        datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")

    response = HttpResponseRedirect(url)
    response.set_cookie("message", lfc_quote(msg), max_age=max_age, expires=expires)

    return response

def get_top_page(page):
    """Returns the top page (The page which is a parent of the given page and
    direct children of the portal.
    """
    while page.parent is not None:
        page = page.parent
    return page

# TODO: Not used at the moment - what to do?
def get_related_pages_by_tags(page, num=None):
    """Returns a dict with related products by tags.

    This is just a thin wrapper for the get_related method of the
    TaggedItem manager of the tagging product in order to provide caching.
    From the tagging product's doc string (mutatis mutantis):

    Returns a list of products which share tags with the product with passed id
    ordered by the number of shared tags in descending order.

    See there for more.
    """
    # Try to get it out of cache
    cache_key = "related-page-by-tags-%s" % page.id
    related_pages = cache.get(cache_key)
    if related_pages is not None:
        return {"related_pages" : related_pages}

    # Create related pages
    related_pages = TaggedItem.objects.get_related(page, Page, num)

    # Save related pages to cache
    cache.set(cache_key, related_pages)

    return {"related_pages" : related_pages}

def traverse_object(request, slug):
    """Traverses to given slug to get the object.
    """
    paths = slug.split("/")
    language = translation.get_language()

    try:
        obj = lfc.models.BaseContent.objects.restricted(request).get(slug=paths[0], parent=None, language__in = ("0", language))
    except lfc.models.BaseContent.DoesNotExist:
        raise Http404

    for path in paths[1:]:
        try:
            obj = obj.sub_objects.restricted(request).filter(slug=path)[0]
        except IndexError:
            raise Http404

    return obj

def get_content_object(*args, **kwargs):
    """Returns the specific content object based on given parameters.
    """
    queryset = _get_queryset(lfc.models.BaseContent)
    object = queryset.get(*args, **kwargs)
    return object.get_content_object()