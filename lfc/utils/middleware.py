import sys
import tempfile
import hotshot
import hotshot.stats
from cStringIO import StringIO

# django imports
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils import translation

# lfc imports
from lfc.utils import traverse_object
from lfc.utils import get_portal
from lfc.models import BaseContent

class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode,
    but you really shouldn't add this middleware to any production configuration.
    * Only tested on Linux
    """
    def process_request(self, request):
        if request.GET.has_key('prof'):
            self.tmpfile = tempfile.NamedTemporaryFile()
            self.prof = hotshot.Profile(self.tmpfile.name)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.GET.has_key('prof'):
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if request.GET.has_key('prof'):
            self.prof.close()

            out = StringIO()
            old_stdout = sys.stdout
            sys.stdout = out

            stats = hotshot.stats.load(self.tmpfile.name)
            # stats.strip_dirs()
            stats.sort_stats('cumulative', )
            # stats.sort_stats('time', )
            stats.print_stats()

            sys.stdout = old_stdout
            stats_str = out.getvalue()

            if response and response.content and stats_str:
                response.content = "<pre>" + stats_str + "</pre>"

        return response


class AJAXSimpleExceptionResponse:
    def process_exception(self, request, exception):
        if settings.DEBUG:
            if request.is_ajax():
                import sys, traceback
                (exc_type, exc_info, tb) = sys.exc_info()
                response = "%s\n" % exc_type.__name__
                response += "%s\n\n" % exc_info
                response += "TRACEBACK:\n"
                for tb in traceback.format_tb(tb):
                    response += "%s\n" % tb
                return HttpResponseServerError(response)

from threading import local
_thread_locals = local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class LFCMiddleware:
    """Traverses the requested object, store this within request.META and sets
    the correct language.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        _thread_locals.user = getattr(request, 'user', None)

        slug = view_kwargs.get("slug")
        if slug is None:
            return

        language = view_kwargs.get("language")
        if language:
            translation.activate(language)
        else:
            translation.activate(settings.LANGUAGE_CODE)

        if slug != "":
            obj = traverse_object(request, view_kwargs.get("slug"))
        else:
            portal = get_portal()
            if portal.standard:
                # using BaseContentManager
                obj = get_object_or_404(BaseContent, portal=portal)
                if obj.language != language:
                    if obj.is_canonical():
                        t = obj.get_translation(language)
                        if t:
                            obj = t
                    else:
                        canonical = obj.get_canonical()
                        if canonical:
                            obj = canonical
                request.META["lfc_context"] = obj.get_specific_type()
            else:
                obj = portal

        request.META["lfc_context"] = obj.get_specific_type()