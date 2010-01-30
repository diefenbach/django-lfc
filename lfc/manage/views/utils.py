# django imports
from django.conf import settings

# lfc imports
from lfc.models import BaseContent

def _update_positions(obj, take_parent=False):
    """Updates position of given object's children. If take_parent is True
    the children of the given object's parent are updated.
    """
    if take_parent == True:
        parent = obj.parent
    else:
        parent = obj

    for language in settings.LANGUAGES:
        if language[0] == settings.LANGUAGE_CODE:
            objs = BaseContent.objects.filter(parent=parent, language__in=("0", language[0]))
        else:
            objs = BaseContent.objects.filter(parent=parent, language = language[0])

        for i, p in enumerate(objs):
            p.position = (i+1)*10
            p.save()
            if obj and obj.id == p.id:
                obj = p

    return obj
    