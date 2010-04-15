# lfc imports
import lfc.utils
from django.conf import settings
from django.utils import translation

def main(request):
    """context processor for LFC.
    """
    current_language = translation.get_language()
    default_language = settings.LANGUAGE_CODE
    
    is_default_language = default_language == current_language
    if current_language == "0" or is_default_language:
        link_language = ""
    else:
        link_language = current_language
    
    return {
        "PORTAL" : lfc.utils.get_portal(),
        "LFC_MULTILANGUAGE"   : settings.LFC_MULTILANGUAGE,
        "DEFAULT_LANGUAGE"    : default_language,
        "CURRENT_LANGUAGE"    : current_language,
        "IS_DEFAULT_LANGUAGE" : is_default_language,
        "LINK_LANGUAGE"       : link_language, 
    }
