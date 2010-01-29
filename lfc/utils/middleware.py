import sys
import tempfile
import hotshot
import hotshot.stats
from cStringIO import StringIO

# django imports
from django.conf import settings
from django.http import Http404
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils import translation

# lfc imports
from lfc.utils import traverse_object
from lfc.utils import get_portal
from lfc.utils import get_content_object

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

class LFCMiddleware:
    """Traverses the requested object, store this within request.META and sets
    the correct language.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        language = view_kwargs.get("language")
        slug = view_kwargs.get("slug")

        if slug is None and language is None:
            return

        if language:
            # if settings.LFC_MULTILANGUAGE == False:
            #     raise Http404
            if language not in settings.LFC_LANGUAGE_IDS:
                raise Http404

            translation.activate(language)
        else:
            translation.activate(settings.LANGUAGE_CODE)

        if slug:
            obj = traverse_object(request, view_kwargs.get("slug"))
            request.META["lfc_context"] = obj
        else:
            portal = get_portal()
            if portal.standard:
                obj = get_content_object(portal=portal)
                if obj.language != language:
                    if obj.is_canonical():
                        t = obj.get_translation(request, language)
                        if t:
                            obj = t
                    else:
                        canonical = obj.get_canonical(request)
                        if canonical:
                            obj = canonical
                request.META["lfc_context"] = obj
            else:
                request.META["lfc_context"] = portal