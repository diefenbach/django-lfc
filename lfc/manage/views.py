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
from lfc.models import File
from lfc.models import Image
from lfc.utils import LazyEncoder
from lfc.utils import get_portal
from lfc.utils import set_message_cookie
from lfc.utils.registration import get_allowed_subtypes
from lfc.utils.registration import get_info_for

# Dashboard #################################################################
@login_required
def dashboard(request, template_name="lfc/manage/dashboard.html"):
    """
    """
    return render_to_response(template_name, RequestContext(request, {

    }))

# Portal ####################################################################
@login_required
def portal(request, template_name="lfc/manage/portal.html"):
    """Displays the main screen of the portal management.
    """
    content_types = get_allowed_subtypes()
    return render_to_response(template_name, RequestContext(request, {
        "display_content_menu" : len(get_allowed_subtypes()) > 1,
        "content_types" : get_allowed_subtypes(),
        "core_data" : portal_core(request),
        "portlets" : portlets_inline(request, get_portal()),
        "navigation" : navigation(request, None),
        "images" : portal_images(request, as_string=True),
    }))

@login_required
def portal_core(request, template_name="lfc/manage/portal_core.html"):
    """Displays the core data tab.
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
def portal_images(request, as_string=False, template_name="lfc/manage/portal_images.html"):
    """Displays the images tab of the portal management screen.
    """
    obj = get_portal()

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

def add_portal_images(request):
    """Adds images to the portal
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

# Content types #############################################################

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

# Filebrowser ################################################################
def filebrowser(request):
    """Displays files/images of the current object within the file browser
    popup of TinyMCE.
    """
    obj_id = request.GET.get("obj_id")

    try:
        obj = BaseContent.objects.get(pk=obj_id)
    except (BaseContent.DoesNotExist, ValueError):
        obj = None

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
        for base_content in BaseContent.objects.filter(parent=None, language__in=("0", translation.get_language())):
            base_contents.append({
                "title" : base_content.title,
                "url" : base_content.get_absolute_url(),
                "children" : _get_obj_children(request, base_content),
            })

        return render_to_response("lfc/manage/filebrowser_files.html",
            RequestContext(request, {
            "obj_id" : obj_id,
            "files" : files,
            "objs" : base_contents,
        }))

def _get_obj_children(request, obj):
    """
    """
    objs = []
    for obj in obj.sub_objects.filter(active=True):
        objs.append({
            "title" : obj.title,
            "url" : obj.get_absolute_url(),
            "children" : _get_obj_children(request, obj),
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
    object = object_ct.get_object_for_this_type(pk=object_id)

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

        html = portlets_inline(request, object)

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
    object = object_ct.get_object_for_this_type(pk=object_id)

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
                slot_id=slot_id, content=object, portlet=portlet, position=position)

            result = simplejson.dumps({
                "html" : portlets_inline(request, object),
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
        return set_message_cookie(
            request.META.get("HTTP_REFERER"),
            msg = _(u"Portlet has been deleted."))

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

# Objects ###################################################################

@login_required
def add_object(request, language=None, id=None):
    """Adds a object to object with given slug.
    """
    type = request.REQUEST.get("type", "page")
    ct = ContentType.objects.filter(model=type)[0]
    mc = ct.model_class()
    form = mc().form

    try:
        parent_object = BaseContent.objects.get(pk=id)
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
                new_object.content_type = type
                new_object.creator = request.user
                new_object.language = language
                new_object.save()

                _update_positions(new_object)
                url = reverse("lfc_manage_object", kwargs={"id": new_object.id})
                return set_message_cookie(url, msg = _(u"Page has been added."))
        else:
            referer = request.POST.get("referer")
            return HttpResponseRedirect(referer)
    else:
        if parent_object is not None:
            form = form(initial={"parent" : parent_object.id})
        else:
            form = form()

    return render_to_response("lfc/manage/object_add.html", RequestContext(request, {
        "type" : type,
        "name" : get_info_for(type).name,
        "form" : form,
        "language" : language,
        "id" : id,
        "referer" : request.POST.get("referer", request.META.get("HTTP_REFERER")),
        "navigation" : navigation(request, parent_object)
    }))

@login_required
def delete_object(request, id):
    """Deletes object with given id.
    """
    try:
        obj = BaseContent.objects.get(pk = id)
    except BaseContent.DoesNotExist:
        pass
    else:
        # Remove the object from the parent's standard in order not to
        # delete the parent
        parent = obj.parent

        if parent is None:
            parent = get_portal()

        if parent.standard == obj:
            parent.standard = None
            parent.save()

        # Remove the object from translations in order not to delete the
        # translations
        if obj.is_canonical():
            for t in obj.translations.all():
                t.canonical = None
                t.save()

        obj.delete()

    if parent:
        url = reverse("lfc_manage_object", kwargs={"id": parent.id})
    else:
        url = reverse("lfc_manage_portal")

    return set_message_cookie(url, msg = _(u"Page has been deleted."))

@login_required
def manage_object(request, id, template_name="lfc/manage/object.html"):
    """Displays the main screen of an object management interface.
    """
    try:
        obj = lfc.utils.get_content_object(pk=id)
    except BaseContent.DoesNotExist:
        url = reverse("lfc_manage_portal")
        return HttpResponseRedirect(url)

    objs = BaseContent.objects.filter(parent=None)

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
    return render_to_response(template_name, RequestContext(request, {
        "content_types" : content_types,
        "display_content_menu" : len(content_types) > 1,
        "obj" : obj,
        "objs" : objs,
        "translations" : translations,
        "canonical" : canonical,
        "languages" : languages,
        "navigation" : navigation(request, obj),
        "core_data" : core_data(request, id),
        "meta_data" : meta_data(request, id),
        "seo_data" : manage_seo(request, id),
        "images" : images(request, id, as_string=True),
        "files" : files(request, id),
        "comments" : comments(request, obj),
        "portlets" : portlets_inline(request, obj),
        "content_type_name" : get_info_for(obj).name,        
    }))

@login_required
def core_data(request, id, as_string=True, template_name="lfc/manage/object_data.html"):
    """Displays / handles the core data an object.
    """
    base_content = BaseContent.objects.get(pk=id)
    obj_ct = ContentType.objects.filter(model=base_content.content_type)[0]
    obj = base_content.get_content_object()
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
    """Displays / handles the meta data an object.
    """
    obj = lfc.utils.get_content_object(pk=id)

    if request.method == "POST":

        form = MetaDataForm(instance=obj, data=request.POST)

        if form.is_valid():
            form.save()
            form = MetaDataForm(instance=_update_positions(obj))

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
    """Displays / handles the seo data an object.
    """
    obj = BaseContent.objects.get(pk=id)
    obj = obj.get_content_object()

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

# Comments
@login_required
def comments(request, obj, template_name="lfc/manage/object_comments.html"):
    """Displays the comments of an object.
    """
    form = CommentsForm(instance=obj)
    comments = Comment.objects.filter(object_pk = obj.id)

    return render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
        "comments" : comments,
        "form" : form,
    }))

@login_required
def update_comments(request, id, template_name="lfc/manage/object_comments.html"):
    """Deletes comments with given ids (passed by request body).
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

# Files #####################################################################
@login_required
def files(request, id, template_name="lfc/manage/object_files.html"):
    """Displays the files tab of an object.
    """
    obj = BaseContent.objects.get(pk=id)
    return render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
    }))

@login_required
def add_files(request, id):
    """Adds a file to obj with passed id.
    """
    obj = get_object_or_404(BaseContent, pk=id)
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
    """Saves/deletes images with given ids (passed by request body).
    """
    obj = get_object_or_404(BaseContent, pk=id)

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
    """
    """
    obj = BaseContent.objects.get(pk=id)

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
    """
    obj = get_object_or_404(BaseContent, pk=id)
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
    """Saves/deletes images with given ids (passed by request body).
    """
    if id is None:
        obj = get_portal()
    else:
        obj = get_object_or_404(BaseContent, id=id)

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

# Navigation #################################################################
def set_navigation_tree_language(request, language):
    """Sets the language for the navigation tree.
    """
    request.session["nav-tree-lang"] = language
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

@login_required
def navigation(request, obj, start_level=1, template_name="lfc/manage/navigation.html"):
    """Displays the content object structure (navigatin tree).
    """
    nav_tree_lang = request.session.get("nav-tree-lang", settings.LANGUAGE_CODE)

    if obj is None:
        current_objs = []
    else:
        current_objs = [obj]
        current_objs.extend(obj.get_ancestors())

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
    }))

def _navigation_children(request, current_objs, obj, start_level, level=3):
    """Renders the children of the given obj (recursively)
    """
    obj = obj.get_content_object()
    temp = obj.sub_objects.all()

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

# Translation ################################################################
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
        return set_message_cookie(url, _(u"Translation has been canceled."))

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
        return set_message_cookie(url, msg=msg)

    else:
        return translate_object(request, translation_language, canonical.id, form_translation, form_canonical)

def _update_positions(obj):
    """Updates position of top objs or given obj.
    """
    for language in settings.LANGUAGES:
        if language[0] == settings.LANGUAGE_CODE:
            objs = BaseContent.objects.filter(parent=obj.parent, language__in=("0", language[0]))
        else:
            objs = BaseContent.objects.filter(parent=obj.parent, language = language[0])

        for i, p in enumerate(objs):
            p.position = (i+1)*10
            p.save()

    return obj