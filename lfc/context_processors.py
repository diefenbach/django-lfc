# lfc imports
import lfc.utils
from django.conf import settings
from django.utils import translation

def main(request):
    """context processor for LFC.
    """
    current_language = translation.get_language()
    default_language = settings.LANGUAGE_CODE

    return {
        "PORTAL" : lfc.utils.get_portal(),
        "LFC_MULTILANGUAGE"   : settings.LFC_MULTILANGUAGE,
        "DEFAULT_LANGUAGE"    : default_language,
        "CURRENT_LANGUAGE"    : current_language,
        "IS_DEFAULT_LANGUAGE" : default_language == current_language,
    }
