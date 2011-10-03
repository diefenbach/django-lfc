# python imports
import logging

# permissions imports
from permissions.exceptions import Unauthorized

# lfc imports
import lfc.utils

# Load logger
logger = logging.getLogger("default")


class LFCMiddleware:
    """LFC specific middleware.
    """
    def process_exception(self, request, exception):
        """Catches Unauthorized exceptions to display the login form.
        """
        if isinstance(exception, Unauthorized):
            logger.info(u"Unauthorized: %s" % exception.message)
            return lfc.utils.login_form(next=request.META.get("PATH_INFO"))
