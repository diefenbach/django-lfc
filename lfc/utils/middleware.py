# permissions imports
from permissions.exceptions import Unauthorized

# lfc imports
import lfc.utils


class LFCMiddleware:
    """LFC specific middleware.
    """
    def process_exception(self, request, exception):
        """Catches Unauthorized exceptions to display the login form.
        """
        if isinstance(exception, Unauthorized):
            return lfc.utils.login_form(next=request.META.get("PATH_INFO"))
