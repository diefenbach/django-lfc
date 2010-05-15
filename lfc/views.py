# python imports
import sys
import traceback

# django imports
from django import template
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# lfc imports
import lfc.utils
from lfc.utils import MessageHttpResponseRedirect
from lfc.models import File
from lfc.models import BaseContent
from lfc.models import Portal

# workflows imports
from workflows.models import Transition

# tagging imports
from tagging.models import TaggedItem
from tagging.utils import get_tag

def portal(request, obj, template_name="lfc/portal.html"):
    """Displays the the portal.
    """
    return render_to_response(template_name, RequestContext(request, {
        "portal" : lfc.utils.get_portal()
    }))

def base_view(request, language=None, slug=None, obj=None):
    """Displays the object for given language and slug.
    """
    language = translation.get_language()
    # If the given language is the default language redirect to the url without
    # the language code http:/domain.de/de/hurz = http:/domain.de/hurz

    # Get the obj (passed my LFC Middleware)
    obj = request.META.get("lfc_context")

    if obj is None:
        raise Http404()

    if isinstance(obj, Portal):
        return portal(request, obj)

    if lfc.utils.registration.get_info(obj) is None:
        raise Http404()

    if not obj.is_active(request.user):
        raise Http404()

    if not obj.has_permission(request.user, "view"):
        return HttpResponseRedirect(reverse("lfc_login"))

    # Redirect to standard object unless superuser is asking
    if obj.standard and request.user.is_superuser == False:
        url = obj.get_absolute_url()
        return HttpResponseRedirect(url)

    # Template
    template_cache_key = "template-%s-%s" % (obj.content_type, obj.id)
    obj_template = cache.get(template_cache_key)
    if obj_template is None:
        obj_template = obj.get_template()
        cache.set(template_cache_key, obj_template)

    # Children
    children_cache_key = "children-%s-%s" % (obj.content_type, obj.id)
    sub_objects = cache.get(children_cache_key)
    if sub_objects is None:
        # Get sub objects (as LOL if requested)
        if obj_template.children_columns == 0:
            sub_objects = obj.get_children(request)
        else:
            sub_objects = lfc.utils.getLOL(obj.get_children(request), obj_template.children_columns)

        cache.set(children_cache_key, sub_objects)

    # Images
    images_cache_key = "images-%s-%s" % (obj.content_type, obj.id)
    cached_images = cache.get(images_cache_key)
    if cached_images:
        image     = cached_images["image"]
        images    = cached_images["images"]
        subimages = cached_images["subimages"]
    else:
        temp_images = list(obj.images.all())
        if temp_images:
            if obj_template.images_columns == 0:
                images = temp_images
                image = images[0]
                subimages = temp_images[1:]
            else:
                images = lfc.utils.getLOL(temp_images, obj_template.images_columns)
                subimages = lfc.utils.getLOL(temp_images[1:], obj_template.images_columns)
                image = images[0][0]
        else:
            image = None
            images = []
            subimages = []

        cache.set(images_cache_key, {
            "image" : image,
            "images" :  images,
            "subimages" : subimages
        })

    # Files
    files = obj.files.all()

    c = RequestContext(request, {
        "lfc_context" : obj,
        "images" : images,
        "image" : image,
        "subimages" : subimages,
        "files" : files,
        "sub_objects" : sub_objects,
        "portal" : lfc.utils.get_portal(),
    })

    # Render twice. This makes tags within text / short_text possible.
    result = render_to_string(obj_template.path, c)
    result = template.Template("{% load lfc_tags %} " + result).render(c)

    return HttpResponse(result)

def file(request, language=None, id=None):
    """Delivers files to the browser.
    """
    file = get_object_or_404(File, pk=id)
    response = HttpResponse(file.file, mimetype='application/binary')
    response['Content-Disposition'] = 'attachment; filename=%s' % file.title

    return response

def search_results(request, language=None, template_name="lfc/search_results.html"):
    """Displays the search result for passed language and query.
    """
    query = request.GET.get("q")

    if language is None:
        language = settings.LANGUAGE_CODE

    f = Q(exclude_from_search=False) & \
        (Q(language = language) | Q(language="0")) & \
        (Q(searchable_text__icontains=query))

    try:
        obj = BaseContent.objects.get(slug="search-results")
    except BaseContent.DoesNotExist:
        obj = None

    results = lfc.utils.get_content_objects(request, f)

    return render_to_response(template_name, RequestContext(request, {
        "lfc_context" : obj,
        "query" : query,
        "results" : results,
    }))

def set_language(request, language, id=None):
    """Sets the language to the given language

    parameters:

        - language
          the requested language

        - id:
          the id of the current displayed object
    """
    translation.activate(language)

    url = None
    if id:
        obj = BaseContent.objects.get(pk=id)

        # If the language of the current object same as the requested language we
        # just stay on the object.
        if obj.language == language:
            url = obj.get_absolute_url()

        # Coming from a object with neutral language, we stay on this object
        elif obj.language == "0":
            url = obj.get_absolute_url()

        # Coming from a canonical object, we try to get the translation for the
        # given language
        elif obj.is_canonical():
            t = obj.get_translation(request, language)
            if t:
                url = t.get_absolute_url()
            else:
                if language == settings.LANGUAGE_CODE:
                    url = "/"
                else:
                    url = "/" + language

        # Coming from a translation, we try to get the canonical and display
        # the given language
        else:
            canonical = obj.get_canonical(request)
            if canonical:
                url = canonical.get_absolute_url()
            else:
                if language == settings.LANGUAGE_CODE:
                    url = "/"
                else:
                    url = "/" + language
    else:
        portal = lfc.utils.get_portal()
        if language == settings.LANGUAGE_CODE:
            url = "/"
        else:
            url = "/" + language

    response = HttpResponseRedirect(url)

    if translation.check_for_language(language):
        if hasattr(request, 'session'):
            request.session['django_language'] = language
        else:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)

    return response

def do_transition(request, id):
    """Processes passed transition for object with passed id.
    """
    from lfc.manage.views import do_transition
    do_transition(request, id)

    obj = BaseContent.objects.get(pk=id)
    return MessageHttpResponseRedirect(obj.get_absolute_url(), _(u"State has been changed."))

def lfc_tagged_object_list(request, slug, tag, template_name="lfc/page_list.html"):
    """
    """
    if tag is None:
        raise AttributeError(_('tagged_object_list must be called with a tag.'))

    tag_instance = get_tag(tag)
    if tag_instance is None:
        raise Http404(_('No Tag found matching "%s".') % tag)

    obj = request.META.get("lfc_context")
    queryset = BaseContent.objects.filter(parent=obj)
    objs = TaggedItem.objects.get_by_model(queryset, tag_instance)

    return render_to_response(template_name, RequestContext(request, {
        "slug" : slug,
        "lfc_context" : obj,
        "objs" : objs,
        "tag" : tag,
    }));

def fiveohoh(request, template_name="500.html"):
    """Handler for 500 server errors. Mails the error to ADMINS.
    """
    exc_type, exc_info, tb = sys.exc_info()
    response = "%s\n" % exc_type.__name__
    response += "%s\n" % exc_info
    response += "TRACEBACK:\n"
    for tb in traceback.format_tb(tb):
        response += "%s\n" % tb

    response += "\nREQUEST:\n%s" % request

    try:
        from_email = settings.ADMINS[0][1]
        to_emails = [a[1] for a in settings.ADMINS]
    except IndexError:
        pass
    else:
        mail = EmailMessage(
            subject="Error LFC", body=response, from_email=from_email, to=to_emails)
        mail.send(fail_silently=True)

    return base_view(request, slug="500")
