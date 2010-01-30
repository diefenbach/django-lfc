# django imports
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

# lfc imports
from lfc.models import BaseContent
from lfc.utils import MessageHttpResponseRedirect

# utils
from lfc.manage.views.utils import _update_positions

@login_required
def translate_object(request, language, id=None, form_translation=None, form_canonical=None, template_name="lfc/manage/object_translate.html"):
    """Dislays the translation form for the object with given id and language
    """
    obj = get_object_or_404(BaseContent, pk=id)

    if obj.is_canonical():
        canonical = obj
        try:
            translation = obj.translations.filter(language=language)[0]
            translation_id = translation.id
        except IndexError:
            translation = None
            translation_id = ""
    else:
        translation = obj
        canonical = obj.canonical
        translation_id = translation.id

    if form_canonical is None:
        form_canonical = canonical.get_content_object().form(instance=canonical.get_content_object(), prefix="canonical")

    if translation:
        translation = translation.get_content_object()

    if form_translation is None:
        form_translation = canonical.get_content_object().form(instance=translation, prefix = "translation")

    return render_to_response(template_name, RequestContext(request, {
        "canonical" : canonical,
        "form_canonical" : form_canonical,
        "form_translation" : form_translation,
        "id" : id,
        "translation_language" : language,
        "translation_id" : translation_id,
    }))

@login_required
def save_translation(request):
    """Adds or edits a translation.
    """
    canonical_id = request.POST.get("canonical_id")

    if request.POST.get("cancel"):
        url = reverse("lfc_manage_object", kwargs={"id" : canonical_id})
        msg = _(u"Translation has been canceled.")
        return MessageHttpResponseRedirect(url, msg)

    canonical = BaseContent.objects.get(pk=canonical_id)
    canonical = canonical.get_content_object()

    try:
        translation_id = request.POST.get("translation_id")
        translation = BaseContent.objects.get(pk=translation_id)
        translation = translation.get_content_object()
        translation_language = translation.language
        msg = _(u"Translation has been updated.")
    except (BaseContent.DoesNotExist, ValueError):
        translation = None
        translation_language = request.POST.get("translation_language")
        msg = _(u"Translation has been added.")

    # Get parent obj
    # 1. Take the translation of the parent if it available in requested language
    # 2. If not, take the parent of the canonical if it's in neutral language
    # 3. If not, don't take a parent at all
    parent = canonical.parent
    if parent == None:
        parent_translation = None
    else:
        try:
            parent_translation = parent.translations.get(language=translation_language)
        except (BaseContent.DoesNotExist):
            if parent.language == "0":
                parent_translation = parent
            else:
                parent_translation = None

    # Get standard obj
    try:
        standard = canonical.standard
        standard_translation = standard.translations.filter(language=translation_language)[0]
    except (AttributeError, IndexError):
        standard_translation = None

    form_canonical = canonical.form(
        prefix="canonical",
        instance = canonical,
        data=request.POST,
        files=request.FILES,
    )

    form_translation = canonical.form(
        prefix="translation",
        instance = translation,
        data=request.POST,
        files=request.FILES,
    )

    if form_canonical.is_valid() and form_translation.is_valid():
        translation = form_translation.save()
        translation.language = translation_language
        translation.canonical = canonical
        translation.parent = parent_translation
        translation.standard = standard_translation
        translation.template = canonical.template
        translation.content_type = canonical.content_type
        translation.creator = request.user
        translation.save()

        _update_positions(translation)

        url = reverse("lfc_manage_object", kwargs={"id" : translation.id})
        return MessageHttpResponseRedirect(url, msg)
    else:
        return translate_object(request, translation_language, canonical.id, form_translation, form_canonical)

