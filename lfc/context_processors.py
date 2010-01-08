# lfc imports
import lfc.utils
from django.conf import settings

def main(request):
    """context processor for LFC.
    """
    return {
        "PORTAL" : lfc.utils.get_portal(),
        "LFC_MULTILANGUAGE" : settings.LFC_MULTILANGUAGE,
    }
