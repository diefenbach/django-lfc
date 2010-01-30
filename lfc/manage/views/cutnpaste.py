# python imports
import copy

# django imports
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

# portlets imports
from portlets.models import PortletAssignment

# lfc imports
import lfc.utils
from lfc.models import BaseContent
from lfc.models import File
from lfc.models import Image
from lfc.settings import COPY, CUT
from lfc.utils import MessageHttpResponseRedirect
from lfc.utils.registration import get_allowed_subtypes
from lfc.utils.registration import get_info

# utils
from lfc.manage.views.utils import _update_positions

# Copy  #####################################################################

def lfc_copy(request, id):
    """Puts the object with passed id into the clipboard.
    """
    request.session["clipboard"] = id
    request.session["clipboard_action"] = COPY

    url = reverse("lfc_manage_object", kwargs = { "id" : id })
    msg = _(u"The object has been put to the clipboard.")

    return MessageHttpResponseRedirect(url, msg)

def cut(request, id):
    """Puts the object within passed id into the clipboard and marks action
    as cut.
    """
    request.session["clipboard"] = id
    request.session["clipboard_action"] = CUT

    url = reverse("lfc_manage_object", kwargs = { "id" : id })
    msg = _(u"The object has been put to the clipboard.")

    return MessageHttpResponseRedirect(url, msg)

def paste(request, id=None):
    """paste the object in the clipboard to object with given id.
    """
    if id:
        url = reverse("lfc_manage_object", kwargs = { "id" : id })
    else:
        url = reverse("lfc_manage_portal")

    # Try to get the action
    action = request.session.get("clipboard_action", "")
    if action == "":
        _reset_clipboard(request)

        return HttpResponseRedirect(url)

    # Try to get the source obj
    source_id = request.session.get("clipboard", "")
    if source_id == "":
        _reset_clipboard(request)
        return HttpResponseRedirect(url)
    try:
        source_obj = lfc.utils.get_content_object(pk=source_id)
    except BaseContent.DoesNotExist:
        _reset_clipboard(request)
        msg = _(u"The object doesn't exists anymore.")
        return MessageHttpResponseRedirect(url, msg)

    # Try to get parent if an id has been passed. If no id is passed the
    # parent is the portal.
    if id:
        try:
            parent = lfc.utils.get_content_object(pk=id)
        except BaseContent.DoesNotExist:
            return HttpResponseRedirect(url)
    else:
        parent = None

    # Copy only allowed sub types to target
    allowed_subtypes = get_allowed_subtypes(parent)
    ctr_source = get_info(source_obj)

    if ctr_source not in allowed_subtypes:
        msg = _(u"The object isn't allowed to be pasted here.")
        return MessageHttpResponseRedirect(url, msg)

    # Don't copy to own descendants
    descendants = source_obj.get_descendants()
    if parent in descendants or parent == source_obj:
        msg = _(u"The object can't be pasted in own descendants.")
        return MessageHttpResponseRedirect(url, msg)

    if action == CUT:
        source_obj.parent_id = id
        source_obj.slug = _generate_slug(source_obj, parent)
        source_obj.save()
        _reset_clipboard(request)
    else:
        # Here we go ...
        target_obj = copy.deepcopy(source_obj)
        target_obj.pk = None
        target_obj.id = None
        target_obj.parent_id = id
        target_obj.position = 1000

        target_obj.slug = _generate_slug(source_obj, parent)
        target_obj.save()

        _copy_images(source_obj, target_obj)
        _copy_files(source_obj, target_obj)
        _copy_portlets(source_obj, target_obj)
        _copy_descendants(source_obj, target_obj)
        _copy_translations(source_obj, target_obj)

    _update_positions(parent)
    msg = _(u"The object has been pasted.")
    return MessageHttpResponseRedirect(url, msg)

def _generate_slug(source_obj, parent):
    """Generates a unique slug for passed source_obj in passed parent
    """
    # Generate slug for pasted object
    new_slug = source_obj.slug
    try:
        BaseContent.objects.get(slug=new_slug, parent=parent, language=source_obj.language)
    except BaseContent.DoesNotExist:
        pass
    else:
        i = 1
        while 1:
            new_slug = source_obj.slug + "-%s" % i
            try:
                BaseContent.objects.get(slug=new_slug, parent=parent, language=source_obj.language)
            except BaseContent.DoesNotExist:
                break
            i += 1

    return new_slug

def _reset_clipboard(request):
    """Resets the clipboard.
    """
    if request.session.has_key("clipboard"):
        del request.session["clipboard"]
    if request.session.has_key("clipboard_action"):
        del request.session["clipboard_action"]

def _copy_descendants(source_obj, target_obj):
    """Copies all descendants of the passed object.
    """
    for child in source_obj.children.all().get_content_objects():
        new_child = copy.deepcopy(child)
        new_child.pk = None
        new_child.id = None
        new_child.parent = target_obj
        new_child.save()

        _copy_images(child, new_child)
        _copy_files(child, new_child)
        _copy_portlets(child, new_child)
        _copy_descendants(child, new_child)
        _copy_translations(child, new_child)

def _copy_images(source_obj, target_obj):
    """Copies all images from source_obj to target_obj.
    """
    for image in source_obj.images.all():
        new_image = Image(content=target_obj, title=image.title)
        new_image.image.save(image.image.name, image.image.file, save=True)
        new_image.save()

def _copy_files(source_obj, target_obj):
    """Copies all files from source_obj to target_obj.
    """
    for file in source_obj.files.all():
        new_file = File(content=target_obj, title=file.title)
        new_file.file.save(file.file.name, file.file.file, save=True)
        new_file.save()

def _copy_portlets(source_obj, target_obj):
    """Copies all portlets from source_obj to target_obj.
    """
    ct = ContentType.objects.get_for_model(source_obj)
    for pa in PortletAssignment.objects.filter(content_id=source_obj.id, content_type=ct):
        new_pa = copy.deepcopy(pa)
        new_pa.pk = None
        new_pa.id = None
        new_pa.content_id = target_obj.id
        new_pa.save()

def _copy_translations(source_obj, target_obj):
    """Copies all translations from source_obj to target_obj.
    """
    for translation in source_obj.translations.all().get_content_objects():
        new_translation = copy.deepcopy(translation)
        new_translation.pk = None
        new_translation.id = None
        new_translation.slug = _generate_slug(translation, translation.parent)
        new_translation.canonical = target_obj
        new_translation.save()

        _copy_images(translation, new_translation)
        _copy_files(translation, new_translation)
        _copy_portlets(translation, new_translation)
        _copy_descendants(translation, new_translation)
