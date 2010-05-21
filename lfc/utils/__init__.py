# python imports
import datetime
import urllib
import sys

# django settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.utils import simplejson
from django.utils.functional import Promise
from django.utils.encoding import force_unicode
from django.utils import translation

# lfc imports
import lfc.models

# TODO: Checkout Django's new message feature
class MessageHttpResponseRedirect(HttpResponseRedirect):
    """Specific HttpResponseRedirect to set a cookie with a message.
    """
    def __init__(self, redirect_to, message):
        HttpResponseRedirect.__init__(self, redirect_to)

        # We just keep the message two seconds.
        max_age = 2
        expires = datetime.datetime.strftime(
            datetime.datetime.utcnow() +
            datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")

        self.set_cookie("message", lfc_quote(message), max_age=max_age, expires=expires)

def set_message_to_reponse(response, msg):
    """Sets message cookie with passed message to passed response.
    """
    # We just keep the message two seconds.
    max_age = 2
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() +
        datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")

    response.set_cookie("message", lfc_quote(msg), max_age=max_age, expires=expires)
    return response

def return_as_json(html, message):
    """
    """
    return HttpResponse(get_json(html, message))

def get_json(html, message):
    """Returns html and message json encoded.
    """
    return simplejson.dumps({ "html" : html, "message" : message, }, cls = LazyEncoder)

class LazyEncoder(simplejson.JSONEncoder):
    """JSONEncoder which encodes django's lazy i18n strings.

    This is mainly used to return status messages along with content to ajax
    calls.
    """
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return obj

def get_content_object(request=None, *args, **kwargs):
    """Returns specific content object based on passed parameters.

    This method should be used if one wants the specific content object
    instead of the BaseContent object.

    You can consider this as the equivalent to Django's get method.
    """
    obj = lfc.models.BaseContent.objects.get(*args, **kwargs)
    return obj.get_content_object()

def get_content_objects(request=None, *args, **kwargs):
    """Returns specific content objects based on passed parameters.

    This method should be used if one wants the specific content object
    instead of the BaseContent object.

    Takes permissions of the current and start_date and end_date of object
    into account.

    You can consider this as the equivalent to Django's filter method.
    """
    objs = lfc.models.BaseContent.objects.filter(*args, **kwargs)

    result = []

    if request is None or request.user.is_superuser:
        for obj in objs:
            obj = obj.get_content_object()
            if lfc.utils.registration.get_info(obj):
                result.append(obj)
    else:
        for obj in objs:
            obj = obj.get_content_object()
            if lfc.utils.registration.get_info(obj) and \
                obj.has_permission(request.user, "view") and \
                obj.is_active(request.user):
                obj = obj.get_content_object()
                result.append(obj)

    return result

def get_portal(pk=1):
    """Returns the default portal.
    """
    # CACHE
    cache_key = "portal-%s" % pk
    portal = cache.get(cache_key)
    if portal:
        return portal

    # At the moment the default portal should always exist.
    try:
        portal = lfc.models.Portal.objects.get(pk=pk)
    except lfc.models.Portal.DoesNotExist:
        portal = lfc.models.Portal.objects.filter()[0]

    cache.set(cache_key, portal)
    return portal

def login_form():
    """Returns the lfc login form.
    """
    return HttpResponseRedirect(reverse("lfc_login"))

def traverse_object(request, path):
    """Returns the the object with the given path.
    """
    # CACHE
    cache_key = "traverse-obj-%s-%s" % (path, request.user.id)
    obj = cache.get(cache_key)
    if obj:
        return obj

    paths = path.split("/")
    language = translation.get_language()

    try:
        obj = lfc.utils.get_content_object(request, slug=paths[0],
            parent=None, language__in = ("0", language))
    except lfc.models.BaseContent.DoesNotExist:
        raise Http404

    for path in paths[1:]:
        try:
            obj = obj.children.get(slug=path, language__in = ("0", obj.language)).get_content_object()
        except lfc.models.BaseContent.DoesNotExist:
            raise Http404

    cache.set(cache_key, obj)
    return obj

def clear_cache():
    """Clears the complete cache.
    """
    # memcached
    try:
        cache._cache.flush_all()
    except AttributeError:
        pass
    else:
        return

    try:
        cache._cache.clear()
    except AttributeError:
        pass
    try:
        cache._expire_info.clear()
    except AttributeError:
        pass

def import_module(module):
    """Imports module with given dotted name.
    """
    try:
        module = sys.modules[module]
    except KeyError:
        __import__(module)
        module = sys.modules[module]
    return module

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

def lfc_quote(string, encoding="utf-8"):
    """Encodes string to encoding before quoting.
    """
    return urllib.quote(string.encode(encoding))

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
    # CACHE
    cache_key = "related-page-by-tags-%s" % page.id
    related_pages = cache.get(cache_key)
    if related_pages is not None:
        return {"related_pages" : related_pages}

    # Create related pages
    related_pages = TaggedItem.objects.get_related(page, Page, num)

    # Save related pages to cache
    cache.set(cache_key, related_pages)

    return {"related_pages" : related_pages}