# python imports
import copy

# django imports
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.comments.models import Comment
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# portlets imports
from portlets.utils import get_registered_portlets
from portlets.utils import get_slots
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot

# lfc imports
import lfc.utils
from lfc.models import BaseContent
from lfc.models import ContentTypeRegistration
from lfc.manage.forms import CommentsForm
from lfc.manage.forms import MetaDataForm
from lfc.manage.forms import SEOForm
from lfc.manage.forms import PortalCoreForm
from lfc.manage.forms import ContentTypeRegistrationForm
from lfc.models import Application
from lfc.models import File
from lfc.models import Image
from lfc.settings import COPY, CUT
from lfc.utils import LazyEncoder
from lfc.utils import MessageHttpResponseRedirect
from lfc.utils import get_portal
from lfc.utils import import_module
from lfc.utils.registration import get_allowed_subtypes
from lfc.utils.registration import get_info

# Portal #####################################################################
##############################################################################

@login_required
def portal(request, template_name="lfc/manage/portal.html"):
    """Displays the main management screen of the portal with all tabs.
    """
    return render_to_response(template_name, RequestContext(request, {
        "core_data" : portal_core(request),
        "children" : portal_children(request),
        "portlets" : portlets_inline(request, get_portal()),
        "navigation" : navigation(request, None),
        "images" : portal_images(request, as_string=True),
        "menu" : portal_menu(request),
        "display_paste" : _display_paste(request)
    }))

@login_required
def portal_core(request, template_name="lfc/manage/portal_core.html"):
    """Displays the core data tab of the portal.
    """
    portal = get_portal()

    if request.method == "POST":
        form = PortalCoreForm(instance=portal, data=request.POST)
        if form.is_valid():
            form.save()

        html =  render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "portal" : portal,
        }))

        html = (
            ("#data", html),
        )

        result = simplejson.dumps({
            "html" : html,
            "message" : _(u"Portal data has been saved.")},
            cls = LazyEncoder
        )
        result = HttpResponse(result)
    else:
        form = PortalCoreForm(instance=portal)

        result = render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "portal" : portal,
        }))

    return result

@login_required
def portal_children(request, template_name="lfc/manage/portal_children.html"):
    """Displays the children tab of the portal.
    """
    language = request.session.get("nav-tree-lang", settings.LANGUAGE_CODE)
    children = lfc.utils.get_content_objects(parent = None, language__in=("0", language))
    return render_to_string(template_name, RequestContext(request, {
        "children" : children,
        "display_paste" : _display_paste(request),
    }))

@login_required
def portal_images(request, as_string=False, template_name="lfc/manage/portal_images.html"):
    """Displays the images tab of the portal management screen.
    """
    obj = get_portal()

    result = render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
        "images" : obj.images.all(),
    }))

    if as_string:
        return result
    else:
        result = simplejson.dumps({
            "images" : result,
            "message" : _(u"Images has been added."),
        }, cls = LazyEncoder)

        return HttpResponse(result)

def portal_menu(request, template_name="lfc/manage/portal_menu.html"):
    """Displays the manage menu of the portal.
    """
    content_types = get_allowed_subtypes()
    return render_to_string(template_name, RequestContext(request, {
        "display_paste" : _display_paste(request),
        "display_content_menu" : len(get_allowed_subtypes()) > 1,
        "content_types" : get_allowed_subtypes(),
    }))

# actions
def update_portal_children(request):
    """Deletes/Updates the children of the portal with passed ids (via
    request body).
    """
    obj =  get_portal()
    action = request.POST.get("action")
    if action == "delete":
        message = _(u"Objects has been deleted.")
        for key in request.POST.keys():
            if key.startswith("delete-"):
                try:
                    id = key.split("-")[1]
                    child = lfc.utils.get_content_object(pk=id)
                    _remove_fks(child)
                    child.delete()
                except (IndexError, BaseContent.DoesNotExist):
                    pass
    elif action == "copy":
        message = _(u"Objects have been put to the clipboard.")
        ids = []
        for key in request.POST.keys():
            if key.startswith("delete-"):
                id = key.split("-")[1]
                ids.append(id)
            request.session["clipboard"] = ids
            request.session["clipboard_action"] = COPY
    elif action == "cut":
        message = _(u"Objects have been put to the clipboard.")
        ids = []
        for key in request.POST.keys():
            if key.startswith("delete-"):
                id = key.split("-")[1]
                ids.append(id)
            request.session["clipboard"] = ids
            request.session["clipboard_action"] = CUT
    elif action == "paste":
        message = _paste(request, None)
    else:
        message = _(u"Objects has been updated.")
        for key in request.POST.keys():
            if key.startswith("obj_id-"):
                id = key.split("-")[1]
                try:
                    child = BaseContent.objects.get(pk=id)
                except BaseContent.DoesNotExist:
                    pass
                else:
                    position = request.POST.get("position-%s" % id, "")
                    if position != "":
                        try:
                            child.position = position
                        except ValueError:
                            pass
                    child.active = request.POST.get("is_active-%s" % id, 0)
                    child.save()

    _update_positions(None)
    html = (
        ("#children", portal_children(request)),
        ("#navigation", navigation(request, None)),
        ("#menu", portal_menu(request)),
    )

    result = simplejson.dumps({
        "html" : html,
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

def add_portal_images(request):
    """Adds images to the portal.
    """
    obj = get_portal()
    if request.method == "POST":
        for file_content in request.FILES.values():
            image = Image(content=obj, title=file_content.name)
            image.image.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = i+1
        image.save()

    return HttpResponse(portal_images(request, id, as_string=True))

# Filebrowser ################################################################
##############################################################################

def filebrowser(request):
    """Displays files/images of the current object within the file browser
    popup of TinyMCE.
    """
    obj_id = request.GET.get("obj_id")

    try:
        obj = BaseContent.objects.get(pk=obj_id)
    except (BaseContent.DoesNotExist, ValueError):
        obj = None
        language = translation.get_language()
    else:
        language = obj.language

    if request.GET.get("type") == "image":
        portal = get_portal()

        if obj:
            images = obj.images.all()
        else:
            images = []
        return render_to_response("lfc/manage/filebrowser_images.html",
            RequestContext(request, {
            "obj_id" : obj_id,
            "images" : images,
            "portal_images" : portal.images.all(),
        }))
    else:
        if obj:
            files = obj.files.all()
        else:
            files = []
        base_contents = []
        for base_content in BaseContent.objects.filter(parent=None, language__in=("0", language)):
            base_contents.append({
                "title" : base_content.title,
                "url" : base_content.get_absolute_url(),
                "children" : _filebrowser_children(request, base_content),
            })

        return render_to_response("lfc/manage/filebrowser_files.html",
            RequestContext(request, {
            "obj_id" : obj_id,
            "files" : files,
            "objs" : base_contents,
        }))

def _filebrowser_children(request, obj):
    """
    """
    objs = []
    for obj in obj.children.restricted(request):
        objs.append({
            "title" : obj.title,
            "url" : obj.get_absolute_url(),
            "children" : _filebrowser_children(request, obj),
        })

    return render_to_string("lfc/manage/filebrowser_files_children.html", RequestContext(request, {
        "objs" : objs
    }))

def fb_upload_image(request):
    """Uploads an image within filebrowser.
    """
    obj_id = request.POST.get("obj_id")
    obj = BaseContent.objects.get(pk=obj_id)

    if request.method == "POST":
        for file_content in request.FILES.values():
            image = Image(content=obj, title=file_content.name)
            image.image.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = i+1
        image.save()

    url = "%s?obj_id=%s&amp;type=image" % (reverse("lfc_filebrowser"), obj_id)
    return HttpResponseRedirect(url)

def fb_upload_file(request):
    """Uploads file within filebrowser.
    """
    obj_id = request.POST.get("obj_id")
    obj = BaseContent.objects.get(pk=obj_id)

    for file_content in request.FILES.values():
        file = File(content=obj, title=file_content.name)
        file.file.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = i+1
        file.save()

    url = "%s?obj_id=%s" % (reverse("lfc_filebrowser"), obj_id)
    return HttpResponseRedirect(url)

# Portlets ###################################################################
##############################################################################

@login_required
def portlets_inline(request, obj, template_name="lfc/manage/portlets_inline.html"):
    """Displays the assigned portlets for given object.
    """
    portlet_types = get_registered_portlets()
    ct = ContentType.objects.get_for_model(obj)

    parent_for_portlets = obj.get_parent_for_portlets()
    if parent_for_portlets:
        parent_slots = get_slots(parent_for_portlets)
    else:
        parent_slots = None

    return render_to_string(template_name, RequestContext(request, {
        "slots" : get_slots(obj),
        "parent_slots" : parent_slots,
        "parent_for_portlets" : parent_for_portlets,
        "portlet_types" : PortletRegistration.objects.all(),
        "object" : obj,
        "object_type_id" : ct.id,
    }))

@login_required
def update_portlets(request, object_type_id, object_id):
    """Update portlets blocking.
    """
    # Get content type to which the portlet should be added
    object_ct = ContentType.objects.get(pk=object_type_id)
    obj = object_ct.get_object_for_this_type(pk=object_id)

    blocked_slots = request.POST.getlist("block_slot")

    for slot in Slot.objects.all():
        if str(slot.id) in blocked_slots:
            try:
                PortletBlocking.objects.create(
                    slot_id=slot.id, content_type_id=object_type_id, content_id=object_id)
            except IntegrityError:
                pass

        else:
            try:
                pb = PortletBlocking.objects.get(
                    slot=slot, content_type=object_type_id, content_id=object_id)
                pb.delete()
            except PortletBlocking.DoesNotExist:
                pass

        html = portlets_inline(request, obj)

    result = simplejson.dumps({
        "html" : html,
        "message" : _(u"Portlet has been updated.")},
        cls = LazyEncoder
    )
    return HttpResponse(result)

@login_required
def add_portlet(request, object_type_id, object_id, template_name="lfc/manage/portlet_add.html"):
    """Form and logic to add a new portlet to the object with given type and id.
    """
    # Get content type to which the portlet should be added
    object_ct = ContentType.objects.get(pk=object_type_id)
    obj = object_ct.get_object_for_this_type(pk=object_id)

    # Get the portlet type
    portlet_type = request.REQUEST.get("portlet_type", "")

    if request.method == "GET":
        try:
            portlet_ct = ContentType.objects.filter(model=portlet_type.lower())[0]
            mc = portlet_ct.model_class()
            form = mc().form(prefix="portlet")
            return render_to_response(template_name, RequestContext(request, {
                "form" : form,
                "object_id" : object_id,
                "object_type_id" : object_ct.id,
                "portlet_type" : portlet_type,
                "slots" : Slot.objects.all(),
            }))
        except ContentType.DoesNotExist:
            pass
    else:
        try:
            ct = ContentType.objects.filter(model=portlet_type.lower())[0]
            mc = ct.model_class()
            form = mc().form(prefix="portlet", data=request.POST)
            portlet = form.save()

            slot_id = request.POST.get("slot")
            position = request.POST.get("position")
            PortletAssignment.objects.create(
                slot_id=slot_id, content=obj, portlet=portlet, position=position)

            result = simplejson.dumps({
                "html" : portlets_inline(request, obj),
                "message" : _(u"Portlet has been added.")},
                cls = LazyEncoder
            )

            return HttpResponse(result)

        except ContentType.DoesNotExist:
            pass

@login_required
def delete_portlet(request, portletassignment_id):
    """Deletes a portlet for given portlet assignment.
    """
    try:
        pa = PortletAssignment.objects.get(pk=portletassignment_id)
    except PortletAssignment.DoesNotExist:
        pass
    else:
        pa.delete()
        url = request.META.get("HTTP_REFERER")
        msg = _(u"Portlet has been deleted.")
        return MessageHttpResponseRedirect(url, msg)

@login_required
def edit_portlet(request, portletassignment_id, template_name="lfc/manage/portlet_edit.html"):
    """Form and logic to edit the portlet of the given portlet assignment.
    """
    try:
        pa = PortletAssignment.objects.get(pk=portletassignment_id)
    except PortletAssignment.DoesNotExist:
        return ""

    if request.method == "GET":
        slots = []
        for slot in Slot.objects.all():
            slots.append({
                "id" : slot.id,
                "name" : slot.name,
                "selected" : slot.id == pa.slot.id,
            })

        form = pa.portlet.form(prefix="portlet")
        return render_to_response(template_name, RequestContext(request, {
            "form" : form,
            "portletassigment_id" : pa.id,
            "slots" : slots,
            "position" : pa.position,
        }))
    else:
        form = pa.portlet.form(prefix="portlet", data=request.POST)
        portlet = form.save()

        # Save the rest
        pa.slot_id = request.POST.get("slot")
        pa.position = request.POST.get("position")
        pa.save()

        html = portlets_inline(request, pa.content)

        result = simplejson.dumps({
            "html" : html,
            "message" : _(u"Portlet has been saved.")},
            cls = LazyEncoder
        )
        return HttpResponse(result)

# Objects ####################################################################
##############################################################################

@login_required
def add_object(request, language=None, id=None):
    """Adds a new content object to the object with the passed id. if the passed
    id is None th content object is added to the portal.
    """
    type = request.REQUEST.get("type", "page")
    ct = ContentType.objects.filter(model=type)[0]
    mc = ct.model_class()
    form = mc().form

    try:
        parent_object = lfc.utils.get_content_object(pk=id)
    except (BaseContent.DoesNotExist, ValueError):
        parent_object = None

    if language is None:
        language = settings.LANGUAGE_CODE

    if request.method == "POST":
        form = form(data=request.POST, initial={"creator" : request.user})
        if request.POST.get("save"):
            if form.is_valid():
                # figure out language for new object
                if parent_object:
                    language = parent_object.language
                else:
                    language = request.session.get("nav-tree-lang", settings.LANGUAGE_CODE)

                new_object = form.save()
                new_object.parent = parent_object
                new_object.creator = request.user
                new_object.language = language
                new_object.position = 1000
                new_object.save()

                _update_positions(new_object, True)
                url = reverse("lfc_manage_object", kwargs={"id": new_object.id})
                msg = _(u"Page has been added.")
                return MessageHttpResponseRedirect(url, msg)

        else:
            referer = request.POST.get("referer")
            return HttpResponseRedirect(referer)
    else:
        if parent_object is not None:
            form = form(initial={"parent" : parent_object.id})
        else:
            form = form()

    if parent_object:
        parent_object = parent_object.get_content_object()

    return render_to_response("lfc/manage/object_add.html", RequestContext(request, {
        "type" : type,
        "name" : get_info(type).name,
        "form" : form,
        "language" : language,
        "id" : id,
        "referer" : request.POST.get("referer", request.META.get("HTTP_REFERER")),
        "navigation" : navigation(request, parent_object)
    }))

@login_required
def delete_object(request, id):
    """Deletes the content object with passed id.
    """
    try:
        obj = lfc.utils.get_content_object(pk = id)
    except BaseContent.DoesNotExist:
        pass
    else:
        parent = obj.parent
        _remove_fks(obj)
        obj.delete()

    if parent:
        url = reverse("lfc_manage_object", kwargs={"id": parent.id})
    else:
        url = reverse("lfc_manage_portal")

    msg = _(u"Page has been deleted.")
    return MessageHttpResponseRedirect(url, msg)

@login_required
def manage_object(request, id, template_name="lfc/manage/object.html"):
    """Displays the main management screen with all tabs of the content object
    with passed id.
    """
    try:
        obj = lfc.utils.get_content_object(pk=id)
    except BaseContent.DoesNotExist:
        url = reverse("lfc_manage_portal")
        return HttpResponseRedirect(url)

    return render_to_response(template_name, RequestContext(request, {
        "navigation" : navigation(request, obj),
        "menu" : object_menu(request, obj),
        "core_data" : core_data(request, id),
        "meta_data" : meta_data(request, id),
        "seo_data" : manage_seo(request, id),
        "images" : images(request, id, as_string=True),
        "files" : files(request, id),
        "comments" : comments(request, obj),
        "portlets" : portlets_inline(request, obj),
        "children" : children(request, obj),
        "content_type_name" : get_info(obj).name,
        "display_paste" : _display_paste(request),
    }))

def object_menu(request, obj, template_name="lfc/manage/object_menu.html"):
    """Displays the manage menu for the passed object.
    """
    if obj.is_canonical():
        canonical = obj
    else:
        canonical = obj.canonical

    languages = []
    for language in settings.LANGUAGES:
        if language[0] != settings.LANGUAGE_CODE:
            languages.append({
                "code" : language[0],
                "name" : language[1],
            })

    if canonical:
        translations = canonical.translations.all()
    else:
        translations = None

    content_types = get_allowed_subtypes(obj)
    
    return render_to_string(template_name, RequestContext(request, {
        "content_types" : content_types,
        "display_content_menu" : len(content_types) > 1,
        "translations" : translations,
        "languages" : languages,
        "canonical" : canonical,
        "obj" : obj,
        "display_paste" : _display_paste(request),
    }))

@login_required
def core_data(request, id, template_name="lfc/manage/object_data.html"):
    """Displays/Updates the core data tab of the content object with passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj_ct = ContentType.objects.filter(model=obj.content_type)[0]

    Form = obj.form

    if request.method == "POST":
        form = Form(instance=obj, data=request.POST)
        if form.is_valid():
            form.save()

        html =  render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "obj" : obj,
        }))

        html = (
            ("#data", html),
            ("#navigation", navigation(request, obj)),
        )

        result = simplejson.dumps({
            "html" : html,
            "message" : _(u"Data has been saved."),
        }, cls = LazyEncoder)
        result = HttpResponse(result)
    else:
        form = Form(instance=obj)

        result = render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "obj" : obj,
        }))

    return result

@login_required
def meta_data(request, id, template_name="lfc/manage/object_meta_data.html"):
    """Displays/Updates the meta tab of the content object with passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)

    if request.method == "POST":

        form = MetaDataForm(instance=obj, data=request.POST)

        if form.is_valid():
            form.save()
            form = MetaDataForm(instance=_update_positions(obj, True))

        html =  render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "obj" : obj,
        }))

        html = (
            ("#meta_data", html),
            ("#navigation", navigation(request, obj)),
        )
        result = simplejson.dumps({
            "html" : html,
            "message" : _(u"Meta data has been saved."),
        }, cls = LazyEncoder)

        result = HttpResponse(result)

    else:
        form = MetaDataForm(instance=obj)

        result = render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "obj" : obj,
        }))

    return result

@login_required
def manage_seo(request, id, template_name="lfc/manage/object_seo.html"):
    """Displays/Updates the SEO tab of the content object with passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)

    if request.method == "POST":
        form = SEOForm(instance=obj, data=request.POST)
        if form.is_valid():
            form.save()

        html =  render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "obj" : obj,
        }))

        html = (
            ("#seo", html),
        )
        result = simplejson.dumps({
            "html" : html,
            "message" : _(u"SEO has been saved."),
        }, cls = LazyEncoder)

        return HttpResponse(result)
    else:
        form = SEOForm(instance=obj)
        return render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "obj" : obj,
        }))

@login_required
def children(request, obj, template_name="lfc/manage/object_children.html"):
    """Displays the children of the passed content object.
    """
    children = obj.children.all()
    return render_to_string(template_name, RequestContext(request, {
        "children" : children,
        "obj" : obj,
        "display_paste" : _display_paste(request),
    }))

@login_required
def update_children(request, id):
    """Deletes/Updates children for the content object with the passed id.The
    to updated children ids are passed within the request.
    """
    obj = lfc.utils.get_content_object(pk=id)

    action = request.POST.get("action")
    if action == "delete":
        message = _(u"Objects have been deleted.")
        for key in request.POST.keys():
            if key.startswith("delete-"):
                try:
                    id = key.split("-")[1]
                    child = lfc.utils.get_content_object(pk=id)
                    _remove_fks(child)
                    child.delete()
                except (IndexError, BaseContent.DoesNotExist):
                    pass
    elif action == "copy":
        message = _(u"Objects have been put to the clipboard.")
        ids = []
        for key in request.POST.keys():
            if key.startswith("delete-"):
                id = key.split("-")[1]
                ids.append(id)
            request.session["clipboard"] = ids
            request.session["clipboard_action"] = COPY
    elif action == "cut":
        message = _(u"Objects have been put to the clipboard.")
        ids = []
        for key in request.POST.keys():
            if key.startswith("delete-"):
                id = key.split("-")[1]
                ids.append(id)
            request.session["clipboard"] = ids
            request.session["clipboard_action"] = CUT
    elif action == "paste":
        message = _paste(request, id)
    else:
        message = _(u"Objects have been updated.")
        for key in request.POST.keys():
            if key.startswith("obj_id-"):
                id = key.split("-")[1]
                try:
                    child = BaseContent.objects.get(pk=id)
                except BaseContent.DoesNotExist:
                    pass
                else:
                    position = request.POST.get("position-%s" % id, "")
                    if position != "":
                        try:
                            child.position = position
                        except ValueError:
                            pass
                    child.active = request.POST.get("is_active-%s" % id, 0)
                    child.save()

    _update_positions(obj)
    html = (
        ("#navigation", navigation(request, obj.get_content_object())),
        ("#children", children(request, obj)),
        ("#menu", object_menu(request, obj)),
    )

    result = simplejson.dumps({
        "html" : html,
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

# Comments ###################################################################
##############################################################################
@login_required
def comments(request, obj, template_name="lfc/manage/object_comments.html"):
    """Displays the comments tab of the passed object.
    """
    form = CommentsForm(instance=obj)
    comments = Comment.objects.filter(object_pk = obj.id)

    return render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
        "comments" : comments,
        "form" : form,
    }))

@login_required
def update_comments(request, id):
    """Deletes/Updates comments from the object with passed id. The to updated
    comment ids are passed passed by request body.
    """
    obj = get_object_or_404(BaseContent, pk=id)

    action = request.POST.get("action")
    if action == "allow_comments":
        form = CommentsForm(instance=obj, data=request.POST)
        form.save()
        message = _(u"Allow comments state has been saved.")
    elif action == "delete":
        message = _(u"Comments has been deleted.")
        for key in request.POST.keys():
            if key.startswith("delete-"):
                try:
                    id = key.split("-")[1]
                    comment = Comment.objects.get(pk=id).delete()
                except (IndexError, Comment.DoesNotExist):
                    pass

    else:
        message = _(u"Comments has been updated.")
        for key in request.POST.keys():
            if key.startswith("comment_id-"):
                id = key.split("-")[1]
                try:
                    comment = Comment.objects.get(pk=id)
                except Comment.DoesNotExist:
                    pass
                else:
                    comment.is_public = request.POST.get("is_public-%s" % id, 0)
                    comment.save()

    html = (
        ("#comments", comments(request, obj)),
    )

    result = simplejson.dumps({
        "html" : html,
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

# Files ######################################################################
##############################################################################
@login_required
def files(request, id, template_name="lfc/manage/object_files.html"):
    """Displays the files tab of the object with the passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)
    return render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
    }))

@login_required
def add_files(request, id):
    """Adds files to the object with the passed id. The to added files are passed
    within the request.
    """
    obj = lfc.utils.get_content_object(pk=id)
    if request.method == "POST":
        for file_content in request.FILES.values():
            file = File(content=obj, title=file_content.name)
            file.file.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = i+1
        file.save()

    return HttpResponse(files(request, id))

@login_required
def update_files(request, id):
    """Saves/deletes files with for the object with the passed id. The to
    updated file ids are passed within the request.
    """
    obj = lfc.utils.get_content_object(pk=id)

    action = request.POST.get("action")
    if action == "delete":
        message = _(u"Files has been deleted.")
        for key in request.POST.keys():
            if key.startswith("delete-"):
                try:
                    temp_id = key.split("-")[1]
                    image = File.objects.get(pk=temp_id).delete()
                except (IndexError, File.DoesNotExist):
                    pass

    elif action == "update":
        message = _(u"Files has been updated.")
        for key, value in request.POST.items():
            if key.startswith("title-"):
                temp_id = key.split("-")[1]
                try:
                    file = File.objects.get(pk=temp_id)
                except File.DoesNotExist:
                    pass
                else:
                    file.title = value
                    file.save()

            elif key.startswith("position-"):
                try:
                    temp_id = key.split("-")[1]
                    file = File.objects.get(pk=temp_id)
                except (IndexError, File.DoesNotExist):
                    pass
                else:
                    file.position = value
                    file.save()

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = i+1
        file.save()

    result = simplejson.dumps({
        "files" : files(request, id),
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

# Images #####################################################################

@login_required
def images(request, id, as_string=False, template_name="lfc/manage/object_images.html"):
    """Displays the images tab of a content object.
    """
    obj = lfc.utils.get_content_object(pk=id)

    result = render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
    }))

    if as_string:
        return result
    else:
        result = simplejson.dumps({
            "images" : result,
            "message" : _(u"Images has been added."),
        }, cls = LazyEncoder)

        return HttpResponse(result)

def add_images(request, id):
    """Adds images to the object with the given id.

    The images are passed within the request body (request.FILES).
    """
    obj = lfc.utils.get_content_object(pk=id)

    if request.method == "POST":
        for file_content in request.FILES.values():
            image = Image(content=obj, title=file_content.name)
            image.image.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = i+1
        image.save()

    return HttpResponse(images(request, id, as_string=True))

@login_required
def update_images(request, id=None):
    """Saves/deletes images for content object with passed id or the portal
    (if id is None).

    The to deleted images are passed within the request body.
    """
    if id is None:
        obj = get_portal()
    else:
        obj = lfc.utils.get_content_object(pk=id)
    action = request.POST.get("action")
    if action == "delete":
        message = _(u"Images has been deleted.")
        for key in request.POST.keys():
            if key.startswith("delete-"):
                try:
                    temp_id = key.split("-")[1]
                    image = Image.objects.get(pk=temp_id).delete()
                except (IndexError, Image.DoesNotExist):
                    pass

    elif action == "update":
        message = _(u"Images has been updated.")
        for key, value in request.POST.items():
            if key.startswith("title-"):
                temp_id = key.split("-")[1]
                try:
                    image = Image.objects.get(pk=temp_id)
                except Image.DoesNotExist:
                    pass
                else:
                    image.title = value
                    image.save()

            elif key.startswith("position-"):
                try:
                    temp_id = key.split("-")[1]
                    image = Image.objects.get(pk=temp_id)
                except (IndexError, Image.DoesNotExist):
                    pass
                else:
                    image.position = value
                    image.save()

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = i+1
        image.save()

    if id is None:
        images_inline = portal_images(request, as_string=True)
    else:
        images_inline = images(request, id, as_string=True)

    result = simplejson.dumps({
        "images" : images_inline,
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

# Navigation tree ############################################################
##############################################################################

@login_required
def navigation(request, obj, start_level=1, template_name="lfc/manage/navigation.html"):
    """Displays the navigation tree of the management interfaces.
    """
    nav_tree_lang = request.session.get("nav-tree-lang", settings.LANGUAGE_CODE)

    if obj is None:
        current_objs = []
        is_portal = True
    else:
        current_objs = [obj]
        current_objs.extend(obj.get_ancestors())
        is_portal = False

    # Display all objs which are neutral or in default language
    q = Q(parent = None) & Q(language__in = ("0", nav_tree_lang))

    temp = BaseContent.objects.filter(q)

    objs = []
    for obj in temp:
        obj = obj.get_content_object()

        if obj in current_objs:
            children = _navigation_children(request, current_objs, obj, start_level)
            is_current = True
        else:
            children = ""
            is_current = False

        translations = []
        objs.append({
            "id" : obj.id,
            "title" : obj.title,
            "is_current" : is_current,
            "children" : children,
            "level" : 2,
            "translations" : obj.translations.all(),
        })

    languages = []
    for language in settings.LANGUAGES:
        if nav_tree_lang == language[0]:
            current_language = language[1]
        languages.append({
            "code" : language[0],
            "name" : language[1],
        })

    return render_to_string(template_name, RequestContext(request, {
        "objs" : objs,
        "show_level" : start_level==2,
        "level" : 2,
        "languages" : languages,
        "current_language": current_language,
        "is_portal" : is_portal,
    }))

def _navigation_children(request, current_objs, obj, start_level, level=3):
    """Renders the children of the given obj (recursively)
    """
    obj = obj.get_content_object()
    temp = obj.children.all()

    objs = []
    for obj in temp:
        obj = obj.get_content_object()
        if obj in current_objs:
            children = _navigation_children(request, current_objs, obj, start_level, level+1)
            is_current = True
        else:
            children = ""
            is_current = False

        objs.append({
            "id" : obj.id,
            "title" : obj.title,
            "is_current" : is_current,
            "children" : children,
            "level" : level,
        })

    result = render_to_string("lfc/manage/navigation_children.html", {
        "objs" : objs,
        "show_level" : level >= start_level,
        "level" : level,
    })

    return result

# actions
def set_navigation_tree_language(request, language):
    """Sets the language for the navigation tree.
    """
    request.session["nav-tree-lang"] = language
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

# Translations ###############################################################
##############################################################################
@login_required
def translate_object(request, language, id=None, form_translation=None,
    form_canonical=None, template_name="lfc/manage/object_translate.html"):
    """Dislays the translation form for the object with passed id and language.
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
    """Saves (adds or edits) a translation.
    """
    canonical_id = request.POST.get("canonical_id")

    if request.POST.get("cancel"):
        url = reverse("lfc_manage_object", kwargs={"id" : canonical_id})
        _(u"Translation has been canceled.")
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

# Template ###################################################################
##############################################################################
def set_template(request):
    """Sets the template of the current object
    """
    obj_id = request.POST.get("obj_id")
    template_id = request.POST.get("template_id")

    obj = BaseContent.objects.get(pk=obj_id)
    obj.template_id = template_id
    obj.save()

    return HttpResponseRedirect(obj.get_absolute_url())

# Cut/Copy and paste #########################################################
##############################################################################

def lfc_copy(request, id):
    """Puts the object with passed id into the clipboard.
    """
    request.session["clipboard"] = [id]
    request.session["clipboard_action"] = COPY

    url = reverse("lfc_manage_object", kwargs = { "id" : id })
    msg = _(u"The object has been put to the clipboard.")

    return MessageHttpResponseRedirect(url, msg)

def cut(request, id):
    """Puts the object within passed id into the clipboard and marks action
    as cut.
    """
    request.session["clipboard"] = [id]
    request.session["clipboard_action"] = CUT

    url = reverse("lfc_manage_object", kwargs = { "id" : id })
    msg = _(u"The object has been put to the clipboard.")

    return MessageHttpResponseRedirect(url, msg)

def paste(request, id=None):
    """Paste the object in the clipboard to object with given id.
    """
    if id:
        url = reverse("lfc_manage_object", kwargs = { "id" : id })
    else:
        url = reverse("lfc_manage_portal")

    msg = _paste(request, id)
    return MessageHttpResponseRedirect(url, msg)

def _paste(request, id):
    """
    """
    # Try to get the action
    action = request.session.get("clipboard_action", "")
    if action == "":
        _reset_clipboard(request)
        msg = _(u"An error has been occured. Please try again.")
        return msg

    # Get the target object
    if id:
        try:
            target = lfc.utils.get_content_object(pk=id)
        except BaseContent.DoesNotExist:
            msg = _(u"The target object has been deleted in the meanwhile.")
            return msg
    else:
        target = None

    # Get the source objs
    source_ids = request.session.get("clipboard", [])

    error_msg = ""
    for source_id in source_ids:
        try:
            source_obj = lfc.utils.get_content_object(pk=source_id)
        except BaseContent.DoesNotExist:
            error_msg = _(u"Some cut/copied objects has been deleted in the meanwhile.")
            continue

        # Copy only allowed sub types to target
        allowed_subtypes = get_allowed_subtypes(target)
        ctr_source = get_info(source_obj)

        if ctr_source not in allowed_subtypes:
            error_msg = _(u"Some objects are not allowed here.")
            continue

        # Don't copy to own descendants
        descendants = source_obj.get_descendants()
        if target in descendants or target == source_obj:
            error_msg = _(u"The objects can't be pasted in own descendants.")
            break

        if action == CUT:
            source_obj.parent_id = id
            source_obj.slug = _generate_slug(source_obj, target)
            source_obj.save()
            _reset_clipboard(request)
        else:
            # Here we go ...
            target_obj = copy.deepcopy(source_obj)
            target_obj.pk = None
            target_obj.id = None
            target_obj.parent_id = id
            target_obj.position = 1000

            target_obj.slug = _generate_slug(source_obj, target)
            target_obj.save()

            _copy_images(source_obj, target_obj)
            _copy_files(source_obj, target_obj)
            _copy_portlets(source_obj, target_obj)
            _copy_descendants(source_obj, target_obj)
            _copy_translations(source_obj, target_obj)

    _update_positions(target)

    if error_msg:
        msg = error_msg
    else:
        msg = _(u"The object has been pasted.")

    return msg

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

# Content types ##############################################################
##############################################################################
def content_types(request):
    """Redirects to the first content type.
    """
    ctr = ContentTypeRegistration.objects.filter()[0]
    url = reverse("lfc_content_type", kwargs={"id" : ctr.id })
    return HttpResponseRedirect(url)

def content_type(request, id, template_name="lfc/manage/content_types.html"):
    """ Displays the main screen of the content type management.
    """
    ctr = ContentTypeRegistration.objects.get(pk=id)

    if request.method == "POST":
        form = ContentTypeRegistrationForm(data = request.POST, instance=ctr)
        if form.is_valid():
            form.save()
    else:
        form = ContentTypeRegistrationForm(instance=ctr)

    return render_to_response(template_name, RequestContext(request, {
        "types" : ContentTypeRegistration.objects.all(),
        "ctr" : ctr,
        "form" : form,
    }))

# Applications ###############################################################
##############################################################################
def applications(request, template_name="lfc/manage/applications.html"):
    """Displays install/uninstall applications view.
    """
    applications = []
    for app_name in settings.INSTALLED_APPS:
        module = import_module(app_name)
        if hasattr(module, "install"):
            try:
                Application.objects.get(name=app_name)
            except Application.DoesNotExist:
                installed = False
            else:
                installed = True

            applications.append({
                "name" : app_name,
                "installed" : installed,
                "pretty_name" : getattr(module, "name", app_name),
                "description" : getattr(module, "description", None),
            })

    url = reverse("lfc_applications")
    return render_to_response(template_name, RequestContext(request, {
        "applications" : applications,
    }))

def install_application(request, name):
    """Installs LFC application with passed name.
    """
    import_module(name).install()
    try:
        Application.objects.create(name=name)
    except Application.DoesNotExist:
        pass

    url = reverse("lfc_applications")
    return HttpResponseRedirect(url)

def reinstall_application(request, name):
    """Reinstalls LFC application with passed name.
    """
    import_module(name).uninstall()
    import_module(name).install()
    try:
        Application.objects.create(name=name)
    except IntegrityError:
        pass

    url = reverse("lfc_applications")
    return HttpResponseRedirect(url)

def uninstall_application(request, name):
    """Uninstalls LFC application with passed name.
    """
    import_module(name).uninstall()

    try:
        application = Application.objects.get(name=name)
    except Application.DoesNotExist:
        pass
    else:
        application.delete()

    url = reverse("lfc_applications")
    return HttpResponseRedirect(url)

def application(request, name, template_name="lfc/manage/application.html"):
    """
    """
    url = reverse("lfc_application", kwargs={ "name" : name })
    return HttpResponseRedirect(url)

def _display_paste(request):
    """Returns true if the paste button should be displayed.
    """
    return request.session.has_key("clipboard")

def _remove_fks(obj):
    """Removes the objects from foreign key fields (in order to not delete
    these related objects)
    """
    parent = obj.parent
    if parent is None:
        parent = get_portal()

    if parent.standard and parent.standard.get_content_object() == obj:
        parent.standard = None
        parent.save()

    if obj.is_canonical():
        for t in obj.translations.all():
            t.canonical = None
            t.save()

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

