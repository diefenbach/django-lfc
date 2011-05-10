# coding=utf-8

# python imports
import datetime
import urllib
import re
import sys
from HTMLParser import HTMLParser

# django settings
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth import BACKEND_SESSION_KEY
from django.contrib.auth import load_backend
from django.contrib.auth.models import AnonymousUser
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

class HttpJsonResponse(HttpResponse):
    def __init__(self, content, mimetype=None, status=None, content_type=None, **kwargs):

        if mimetype is None:
            mimetype = "application/json"

        content = render_to_json(content, **kwargs)

        HttpResponse.__init__(self, content=content,
            mimetype=mimetype, status=status, content_type=content_type)

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

def render_to_json(html, **kwargs):
    """Renders given data to jsnon
    """
    data = { "html" : html }
    data.update(**kwargs)

    return simplejson.dumps(data, cls = LazyEncoder)

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
    parent = kwargs.get("parent")

    if parent and parent.order_by:
        objs = objs.order_by(parent.order_by)

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
    cache_key = "%s-portal-%s" % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, pk)
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

def get_user_from_session_key(session_key):
    """Returns the user from the passed session_key.

    This is a workaround for jquery.upload, which is used to mass upload images
    and files.
    """
    try:
        session_engine = __import__(settings.SESSION_ENGINE, {}, {}, [''])
        session_wrapper = session_engine.SessionStore(session_key)
        user_id = session_wrapper.get(SESSION_KEY)
        auth_backend = load_backend(session_wrapper.get(BACKEND_SESSION_KEY))
        if user_id and auth_backend:
            return auth_backend.get_user(user_id)
        else:
            return AnonymousUser()
    except AttributeError:
        return AnonymousUser()

def login_form(next=None):
    """Returns the lfc login form.
    """
    if next:
        url = "%s?next=%s" % (reverse("lfc_login"), next)
    else:
        url = reverse("lfc_login")

    return HttpResponseRedirect(url)

def traverse_object(request, path):
    """Returns the the object with the given path.
    """
    language = translation.get_language()

    # CACHE
    cache_key = "%s-traverse-obj-%s-%s-%s" % (settings.CACHE_MIDDLEWARE_KEY_PREFIX,
                                              path, request.user.id, language)
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
    cache_key = "%s-related-page-by-tags-%s" % \
                                 (settings.CACHE_MIDDLEWARE_KEY_PREFIX, page.id)
    related_pages = cache.get(cache_key)
    if related_pages is not None:
        return {"related_pages" : related_pages}

    # Create related pages
    related_pages = TaggedItem.objects.get_related(page, Page, num)

    # Save related pages to cache
    cache.set(cache_key, related_pages)

    return {"related_pages" : related_pages}
    
class HTML2TextParser(HTMLParser):
    """HTMLParser to strip all HTML.
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.__text = ""

    def handle_entityref(self, name):
        name = name.replace(u"uuml", u"ü")
        name = name.replace(u"auml", u"ä")
        name = name.replace(u"ouml", u"o")
        name = name.replace(u"Uuml", u"Ü")
        name = name.replace(u"Auml", u"Ä")
        name = name.replace(u"Ouml", u"Ö")
        name = name.replace(u"szlig", u"ß")
        name = name.replace(u"ndash", u"-")
        self.__text += name

    def handle_data(self, data):
        if len(data) > 0:
            data = re.sub('[ \t\r\n]+', ' ', data)
            self.__text += data

    def handle_starttag(self, tag, attrs):
        self.__text += " "

    def handle_endtag(self, tag):
        self.__text += " "

    def text(self):
        return ''.join(self.__text).strip()

def html2text(html):
    """Removes HTML from given html
    """
    parser = HTML2TextParser()
    parser.feed(html)
    parser.close()
    return parser.text()    