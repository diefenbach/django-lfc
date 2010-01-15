# python imports
import datetime

# django import
from django import template
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.template import Node, TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# contact_form imports
from contact_form.forms import ContactForm

# tagging imports
from tagging.managers import ModelTaggedItemManager

# feedparser imports
import feedparser

# lfc imports
import lfc.utils
from lfc.models import BaseContent
from lfc.models import Page

register = template.Library()

class LanguagesNode(Node):
    """
    """
    def render(self, context):
        lfc_context = context.get("lfc_context")
        request = context.get("request")

        languages = []
        for language in settings.LANGUAGES:
            if lfc_context is None:
                is_available = True
            elif lfc_context.has_language(request, language[0]):
                is_available = True
            else:
                is_available = False

            languages.append({
                "code" : language[0],
                "name" : language[1],
                "is_available" : is_available,
            })

        context["lfc_languages"] = languages
        return ''

def do_languages(parser, token):
    """Tag to put the contact form into context.
    """
    bits = token.contents.split()
    len_bits = len(bits)
    if len_bits != 1:
        raise TemplateSyntaxError(_('%s tag needs no argument') % bits[0])

    return LanguagesNode()

register.tag('lfc_languages', do_languages)

class ContactFormNode(Node):
    """Tag to put the contact form into context.
    """
    def render(self, context):
        request = context.get("request")
        if request.method == "POST":
            contact_form = ContactForm(data=request.POST, request=request)
        else:
            contact_form = ContactForm(request=request)

        context["form"] = contact_form
        return ''

def do_contact_form(parser, token):
    """Tag to put the contact form into context.
    """
    bits = token.contents.split()
    len_bits = len(bits)
    if len_bits != 1:
        raise TemplateSyntaxError(_('%s tag needs no argument') % bits[0])

    return ContactFormNode()

register.tag('contact_form', do_contact_form)

@register.inclusion_tag('lfc/tags/tabs.html', takes_context=True)
def tabs(context, page=None):
    """Returns the top level pages as tabs (aka horizontal menu bar).
    """
    if page:
        page = page.get_content_object()

    request = context.get("request")
    language = context.get("LANGUAGE_CODE")

    temp = BaseContent.objects.restricted(request).filter(
        language__in=(language, "0"),
        parent = None,
        exclude_from_navigation=False,
    )

    if page is None:
        current_pages = []
    else:
        current_pages = [page]
        current_pages.extend(page.get_ancestors())

    pages = []
    for page in temp:
        page.current = page.get_content_object() in current_pages
        pages.append(page)

    return {
        "language" : language,
        "pages" : pages,
        "portal" : lfc.utils.get_portal(),
    }

@register.inclusion_tag('lfc/tags/scrollable.html', takes_context=True)
def scrollable(context, tags=None, title=False, text=True, limit=5):
    """Displays objects with given tabs as scrollable
    """
    items = BaseContent.objects.restricted(request)

    if tags:
        items = ModelTaggedItemManager().with_all(tags, items)

    return {
        "items" : items,
        "title" : title,
        "text" : text,
    }

@register.inclusion_tag('lfc/tags/rss.html', takes_context=True)
def rss(context, url, limit=5):
    """An inclusion tag which displays an rss feed.
    """
    feed = feedparser.parse(url)

    try:
        name = feed["feed"]["link"].split("/")[-1]
    except (KeyError, IndexError, AttributeError):
        return {
            "entries" : [],
            "link" : "",
            "LANGUAGE_CODE" : "",
        }

    entries = []
    for entry in feed.entries[0:limit]:
        summary = entry.summary.replace("%s: " % name, "")

        entries.append({
            "title" : entry.title,
            "summary" : summary,
            "date" : datetime.datetime(*entry["updated_parsed"][0:6])
        })

    return {
        "entries" : entries,
        "LANGUAGE_CODE" : context.get("LANGUAGE_CODE"),
        "link" : feed["feed"]["link"],
    }

@register.inclusion_tag('lfc/tags/navigation.html', takes_context=True)
def navigation(context, start_level=1, expand_level=0):
    """Tag to render a navigation tree. This is also reused by the navigation
    portlet.
    """
    request = context.get("request")
    obj = request.META.get("lfc_context")

    language = translation.get_language()

    temp = BaseContent.objects.restricted(request).filter(
        parent = None,
        language__in = (language, "0"),
        exclude_from_navigation=False)

    # Add portal's standard to current_objs
    if obj is None:
        current_objs = []
        standard = lfc.utils.get_portal().standard
        if standard:
            if language != standard.language:
                standard = standard.get_translation(request, language)
            if standard:
                current_objs.append(standard.get_content_object())
    else:
        current_objs = [obj]
        current_objs.extend(obj.get_ancestors())

    objs = []
    for obj in temp:
        obj = obj.get_content_object()
        if obj in current_objs:
            children = _navigation_children(request, current_objs, obj, start_level, expand_level)
            is_current = True
        elif expand_level >= 1 and start_level <= 1:
            children = _navigation_children(request, current_objs, obj, start_level, expand_level)
            is_current = False
        else:
            children = ""
            is_current = False

        objs.append({
            "id" : obj.id,
            "slug" : obj.slug,
            "title" : obj.title,
            "url" : obj.get_absolute_url(),
            "is_current" : is_current,
            "children" : children,
            "level" : 1
        })

    return {
        "objs" : objs,
        "show_level" : start_level==1
    }

def _navigation_children(request, current_objs, obj, start_level, expand_level, level=2):
    """Renders the children of given object as sub navigation tree.
    """
    obj = obj.get_content_object()
    temp = obj.sub_objects.restricted(request).filter(
        exclude_from_navigation = False,
        language__in = (translation.get_language(), "0"),
    )

    objs = []
    for obj in temp:
        obj = obj.get_content_object()
        if obj in current_objs:
            children = _navigation_children(request, current_objs, obj, start_level, expand_level, level=level+1)
            is_current = True
        elif level <= expand_level and level >= start_level:
            children = _navigation_children(request, current_objs, obj, start_level, expand_level, level=level+1)
            is_current = False
        else:
            children = ""
            is_current = False

        objs.append({
            "id" : obj.id,
            "slug" : obj.slug,
            "title" : obj.title,
            "url" : obj.get_absolute_url(),
            "is_current" : is_current,
            "children" : children,
            "level" : level,
        })

    result = render_to_string("lfc/tags/navigation_children.html", {
        "objs" : objs,
        "show_level" : level >= start_level,
    })

    return result

@register.inclusion_tag('lfc/tags/breadcrumbs.html', takes_context=True)
def breadcrumbs(context):
    """Displays breadcrumbs.
    """
    obj = context.get("lfc_context")
    if obj is None:
        return {
            "obj" : None,
            "objs" : []
        }

    objs = []

    temp = obj
    while temp is not None:
        objs.insert(0, temp)
        temp = temp.parent

    return {
        "obj" : obj,
        "objs" : objs,
    }

@register.inclusion_tag('lfc/tags/page.html', takes_context=True)
def page(context, slug, part):
    """Displays the a part (title/text) of the page with passes slug.
    """
    request = context.get("request")
    page = lfc.utils.traverse_object(request, slug)

    if page:
        page = page.get_content_object()

    return { "page" : page, "part": part }

@register.inclusion_tag('lfc/tags/objects.html', takes_context=True)
def objects_by_slug(context, slug):
    """Display all sub objects of the object with given slug
    """
    request = context.get("request")
    try:
        obj = lfc.utils.traverse_object(request, slug)
    except Http404:
        return { "objs" : [] }

    objs = obj.sub_objects.restricted(request)

    return { "objs" : objs }

@register.inclusion_tag('lfc/tags/previous_next.html')
def previous_next_by_date(obj):
    """Displays previous/links by creation date for the given object.
    """
    try:
        previous = obj.get_previous_by_creation_date(parent=obj.parent)
    except ObjectDoesNotExist:
        previous = None

    try:
        next = obj.get_next_by_creation_date(parent=obj.parent)
    except ObjectDoesNotExist:
        next = None

    return {
        "previous" : previous,
        "next" : next,
    }

@register.inclusion_tag('lfc/tags/previous_next.html', takes_context=True)
def previous_next_by_position(context, obj):
    """Displays previous/links by position for the given object.
    """
    request = context.get("request")
    siblings = [o.get_content_object() for o in obj.parent.sub_objects.restricted(request)]
    current_position = siblings.index(obj)
    next_position = current_position + 1
    previous_position = current_position - 1

    if previous_position < 0:
        previous = None
    else:
        try:
            previous = siblings[previous_position]
        except IndexError:
            previous = None

    try:
        next = siblings[next_position]
    except IndexError:
        next = None

    return {
        "previous" : previous,
        "next" : next,
    }