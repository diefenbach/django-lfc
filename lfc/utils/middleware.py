# python imports
from cStringIO import StringIO
import hotshot
import hotshot.stats
import sys
import traceback
import tempfile

# django imports
from django.conf import settings
from django.http import HttpResponseServerError

# permissions imports
from permissions.exceptions import Unauthorized

# lfc imports
import lfc.utils


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
        if "prof" in request.GET.keys():
            self.tmpfile = tempfile.NamedTemporaryFile()
            self.prof = hotshot.Profile(self.tmpfile.name)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if "prof" in request.GET.keys():
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if "prof" in request.GET.keys():
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
                (exc_type, exc_info, tb) = sys.exc_info()
                response = "%s\n" % exc_type.__name__
                response += "%s\n\n" % exc_info
                response += "TRACEBACK:\n"
                for tb in traceback.format_tb(tb):
                    response += "%s\n" % tb
                return HttpResponseServerError(response)


class LFCMiddleware:
    """LFC specific middleware
    """
    def process_exception(self, request, exception):
        """Catches Unauthorized exceptions to display the login form.
        """
        if isinstance(exception, Unauthorized):
            return lfc.utils.login_form(next=request.META.get("PATH_INFO"))
