# python imports
import datetime

# django import
from django import template
from django.core.cache import cache
from django.template import Node, TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# contact_form imports
from contact_form.forms import ContactForm

# tagging imports
from tagging.managers import ModelTaggedItemManager
from tagging.models import TaggedItem

# feedparser imports
import feedparser

# lfc imports
import lfc.utils
from lfc.models import BaseContent
from lfc.models import Page

register = template.Library()

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
    """Returns the top level pages as tabs
    """
    if page:
        page = page.get_specific_type()

    request = context.get("request")
    language = context.get("LANGUAGE_CODE")

    if request.user.is_superuser:
        temp = BaseContent.objects.filter(
            language__in=(language, "0"),
            parent = None,
            exclude_from_navigation=False,
        )
    else:
        temp = BaseContent.objects.filter(
            language__in=(language, "0"),
            active=True,
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
        page.current = page.get_specific_type() in current_pages
        pages.append(page)

    return {
        "language" : language,
        "pages" : pages,
        "portal" : lfc.utils.get_portal(),
    }

@register.inclusion_tag('lfc/tags/scrollable.html', takes_context=True)
def scrollable(context, tags=None, title=False, text=True, limit=5):
    """
    """
    items = Page.objects.all()

    if tags:
        items = ModelTaggedItemManager().with_all(tags, items)

    return {
        "items" : items,
        "title" : title,
        "text" : text,
        "LANGUAGE_CODE" : context.get("LANGUAGE_CODE")
    }

@register.inclusion_tag('lfc/tags/recent.html', takes_context=True)
def recent(context, title=True, text=False):
    """
    """
    items = BaseContent.objects.all()
    return {
        "items" : items,
        "title" : title,
        "text" : text,
        "LANGUAGE_CODE" : context.get("LANGUAGE_CODE")
    }

@register.inclusion_tag('lfc/tags/twitter.html', takes_context=True)
def twitter(context, url):
    """
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
    for entry in feed.entries[0:5]:
        summary = entry.summary.replace("%s: " % name, "")

        entries.append({
            "summary" : summary,
            "date" : datetime.datetime(*entry["updated_parsed"][0:6])
        })

    return {
        "entries" : entries,
        "LANGUAGE_CODE" : context.get("LANGUAGE_CODE"),
        "link" : feed["feed"]["link"],
    }

@register.inclusion_tag('lfc/tags/navigation.html', takes_context=True)
def navigation(context, page=None, start_level=1):
    """
    """
    request = context.get("request")
    page = request.META.get("lfc_context")

    temp = BaseContent.objects.filter(
        parent = None,
        active = True,
        language__in = (translation.get_language(), "0"),
        exclude_from_navigation=False)

    if page is None:
        current_pages = []
    else:
        current_pages = [page]
        current_pages.extend(page.get_ancestors())

    pages = []
    for page in temp:
        page = page.get_specific_type()
        if page in current_pages:
            children = _navigation_children(request, current_pages, page, start_level)
            is_current = True
        else:
            children = ""
            is_current = False

        pages.append({
            "id" : page.id,
            "slug" : page.slug,
            "title" : page.title,
            "url" : page.get_absolute_url(),
            "is_current" : is_current,
            "children" : children,
            "level" : 1
        })

    return {
        "pages" : pages,
        "show_level" : start_level==1
    }

def _navigation_children(request, current_pages, page, start_level, level=2):
    """
    """
    page = page.get_specific_type()
    temp = page.sub_objects.filter(
        active = True,
        exclude_from_navigation = False,
        language__in = (translation.get_language(), "0"),
    )

    pages = []
    for page in temp:
        page = page.get_specific_type()
        if page in current_pages:
            children = _navigation_children(request, current_pages, page, start_level, level+1)
            is_current = True
        else:
            children = ""
            is_current = False

        pages.append({
            "id" : page.id,
            "slug" : page.slug,
            "title" : page.title,
            "url" : page.get_absolute_url(),
            "is_current" : is_current,
            "children" : children,
            "level" : level,
        })

    result = render_to_string("lfc/tags/navigation_children.html", {
        "pages" : pages,
        "show_level" : level >= start_level,
    })

    return result

@register.inclusion_tag('lfc/tags/breadcrumbs.html', takes_context=True)
def breadcrumbs(context):
    """
    """
    obj = context.get("lfc_object")
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

@register.inclusion_tag('lfc/tags/files.html')
def files(files):
    """
    """
    return { "files" : files }

@register.inclusion_tag('lfc/tags/page.html')
def page(slug, part):
    """
    """
    page = Page.objects.get(slug=slug)
    return { "page" : page, "part": part }

@register.inclusion_tag('lfc/tags/previous_next.html')
def previous_next(page, sorting="creation_date"):
    """
    """
    try:
        previous = page.get_previous_by_creation_date(parent=page.parent)
    except (Page.DoesNotExist, IndexError):
        previous = None

    try:
        next = page.get_next_by_creation_date(parent=page.parent)
    except (Page.DoesNotExist, IndexError):
        next = None

    return {
        "previous" : previous,
        "next" : next,
    }

@register.inclusion_tag('lfc/tags/previous_next.html')
def previous_next_by_position(page):
    """
    """
    siblings = list(page.parent.get_sub_pages())
    current_position = siblings.index(page)
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

@register.inclusion_tag('lfc/tags/image.html', takes_context=True)
def image(context, ord):
    """Returns an image with given ord for the current page.
    """
    page = context.get("lfc_object")
    return {
        "image" : page.images.all()[ord-1],
    }

@register.inclusion_tag('lfc/tags/file.html', takes_context=True)
def file(context, ord):
    """Returns an file with given ord for the current page.
    """
    files = context.get("files")

    try:
        file = files[ord-1]
    except IndexError:
        file = None

    return {
        "file" : file,
    }