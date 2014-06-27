# python imports
import copy
import datetime
import json
import urlparse
import re

# django imports
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.comments.models import Comment
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# tagging imports
from tagging.models import Tag

# portlets imports
from portlets.utils import get_slots
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot

# permissions imports
import permissions.utils
from permissions.models import ObjectPermission
from permissions.models import ObjectPermissionInheritanceBlock
from permissions.models import Permission
from permissions.models import PrincipalRoleRelation
from permissions.models import Role

# workflows imports
import workflows.utils
from workflows.models import State
from workflows.models import StateInheritanceBlock
from workflows.models import StateObjectRelation
from workflows.models import StatePermissionRelation
from workflows.models import Transition
from workflows.models import Workflow
from workflows.models import WorkflowPermissionRelation

# lfc imports
import lfc.signals
import lfc.utils
from lfc.models import BaseContent
from lfc.models import ContentTypeRegistration
from lfc.models import Portal
from lfc.models import WorkflowStatesInformation
from lfc.manage.forms import CommentForm
from lfc.manage.forms import CommentsForm
from lfc.manage.forms import ContentTypeRegistrationForm
from lfc.manage.forms import FileForm
from lfc.manage.forms import GroupForm
from lfc.manage.forms import ImageForm
from lfc.manage.forms import PortalCoreForm
from lfc.manage.forms import MetaDataForm
from lfc.manage.forms import RoleForm
from lfc.manage.forms import SEOForm
from lfc.manage.forms import UserForm
from lfc.manage.forms import UserAddForm
from lfc.manage.forms import StateForm
from lfc.manage.forms import TransitionForm
from lfc.manage.forms import WorkflowForm
from lfc.manage.forms import WorkflowAddForm
from lfc.models import Application
from lfc.models import File
from lfc.models import Image
from lfc.settings import COPY, CUT, IMAGE_SIZES
from lfc.utils import LazyEncoder
from lfc.utils import MessageHttpResponseRedirect
from lfc.utils import HttpJsonResponse
from lfc.utils import return_as_json
from lfc.utils import get_portal
from lfc.utils import import_module
from lfc.utils import render_to_json
from lfc.utils.registration import get_allowed_subtypes
from lfc.utils.registration import get_info

# Load logger
import logging
logger = logging.getLogger("default")

# Global #####################################################################
##############################################################################
def add_object(request, language=None, id=None, template_name="lfc/manage/object_add.html"):
    """Displays an add form (GET) and adds a new child content object to the
    object with the passed id (POST). If the passed id is None the content
    object is added to the portal.

    **Parameters:**

        id
            The id of the object to which the new object should be added. If
            None the object will be added to the portal.

    **Query String:**

        type
            The type of the content object which should be added. Default is
            'page'.

    **Permission:**

        add
    """
    type = request.REQUEST.get("type", "page")
    ct = ContentType.objects.filter(model=type)[0]
    mc = ct.model_class()
    form = mc().add_form

    try:
        parent_object = lfc.utils.get_content_object(pk=id)
        parent_object.check_permission(request.user, "add")
    except (BaseContent.DoesNotExist, ValueError):
        parent_object = None
        get_portal().check_permission(request.user, "add")

    if language is None:
        language = settings.LANGUAGE_CODE

    if request.method == "POST":
        form = form(prefix="add", data=request.POST, initial={"creator": request.user})
        if form.is_valid():
            # figure out language for new object
            if parent_object:
                language = parent_object.language
            else:
                language = request.session.get("nav-tree-lang", settings.LANGUAGE_CODE)

            data = form.cleaned_data
            new_object = mc.objects.create(**data)

            # Find unique slug
            i = 1
            slug = new_object.slug
            while BaseContent.objects.filter(slug=new_object.slug, parent=parent_object, language=language).count() > 0:
                new_object.slug = slug + "-%s" % i
                i += 1

            new_object.parent = parent_object
            new_object.creator = request.user
            new_object.language = language

            amount = BaseContent.objects.filter(parent=parent_object, language__in=("0", language)).count()
            new_object.position = (amount + 1) * 10

            new_object.save()

            # Send signal
            lfc.signals.post_content_added.send(new_object)

            _update_positions(new_object, True)

            # Ugly, but works for now. The reason is that object_core
            # called via object_tabs tries to validate the form if the
            # request method is POST.
            request.method = "GET"

            result = json.dumps({
                "tab": 0,
                "url": reverse("lfc_manage_object", kwargs={"id": new_object.id}),
                }, cls=LazyEncoder)

            logger.info("Created New Object: User: %s, ID: %s, Type: %s" % (request.user.username, new_object.id, new_object.get_content_type()))
            return lfc.utils.set_message_to_reponse(
                HttpResponse(result), _(u"Object has been added."))

        else:
            form = render_to_string(template_name, RequestContext(request, {
                "type": type,
                "name": get_info(type).name,
                "form": form,
                "language": language,
                "id": id,
            }))

            html = ((".overlay .content", form),)
            return HttpResponse(render_to_json(html=html, message=_(u"An error has been occured.")))
    else:
        if parent_object is not None:
            form = form(prefix="add", initial={"parent": parent_object.id})
        else:
            form = form(prefix="add")

    if parent_object:
        parent_object = parent_object.get_content_object()

    form = render_to_string("lfc/manage/object_add.html", RequestContext(request, {
        "type": type,
        "name": get_info(type).name,
        "form": form,
        "language": language,
        "id": id,
    }))

    html = ((".overlay .content", form),)

    return HttpJsonResponse(
        content=html,
        open_overlay=True,
        mimetype="text/plain",
    )


def delete_object(request, id):
    """Deletes the content object with passed id.

    **Parameters:**

        id
            The id of the object to which should be deleted.

    **Permission:**

        delete
    """
    try:
        obj = lfc.utils.get_content_object(pk=id)
    except BaseContent.DoesNotExist:
        message = _(u"The object couldn't been deleted.")
    else:
        obj.check_permission(request.user, "delete")

        ctype = ContentType.objects.get_for_model(obj)
        _remove_fks(obj)

        # TODO: Delete tags for deleted object
        Tag.objects.get_for_object(obj).delete()

        # Deletes files on file system
        obj.images.all().delete()
        obj.files.all().delete()

        # Delete workflows stuff
        StateObjectRelation.objects.filter(content_id=obj.id, content_type=ctype).delete()

        # Delete permissions stuff
        ObjectPermission.objects.filter(content_id=obj.id, content_type=ctype).delete()
        ObjectPermissionInheritanceBlock.objects.filter(content_id=obj.id, content_type=ctype).delete()

        # Delete portlets stuff
        for pa in PortletAssignment.objects.filter(content_id=obj.id, content_type=ctype):
            pa.portlet.delete()
            pa.delete()
        PortletBlocking.objects.filter(content_id=obj.id, content_type=ctype).delete()

        logger.info("Deleted Object: User: %s, ID: %s, Type: %s" % (request.user.username, obj.id, obj.get_content_type()))

        obj.delete()
        message = _(u"The object has been deleted.")

    if obj.parent:
        return MessageHttpResponseRedirect(reverse("lfc_manage_object", kwargs={"id": obj.parent.id}), message)
    else:
        return MessageHttpResponseRedirect(reverse("lfc_manage_portal"), message)

# Portal #####################################################################
##############################################################################


def portal(request, template_name="lfc/manage/portal.html"):
    """Displays the main management screen of the portal.

    Builds it out of navigation, menu and tabs.

    **Permission:**

        view_management
    """
    portal = get_portal()
    portal.check_permission(request.user, "view_management")

    return render_to_response(template_name, RequestContext(request, {
        "navigation": navigation(request, None),
        "menu": portal_menu(request, portal),
        "tabs": portal_tabs(request, portal),
    }))


def portal_permissions(request, portal, template_name="lfc/manage/portal_permissions.html"):
    """Displays the permissions tab of the portal.

    **Permission:**

        None (as this is not called from outside)
    """
    permissions_dict = {}
    ct = ContentType.objects.get_for_model(portal)
    for op in ObjectPermission.objects.filter(content_type=ct, content_id=portal.id).values("role_id", "permission_id"):
        role_id = op["role_id"]
        permission_id = op["permission_id"]
        if not permissions_dict.has_key(role_id):
            permissions_dict[role_id] = {}
        permissions_dict[role_id][permission_id] = 1
    all_roles = Role.objects.all().values("id", "name")

    my_permissions = []
    for permission in Permission.objects.order_by("name").values("id", "name", "codename"):
        roles = []
        for role in all_roles:
            try:
                permissions_dict[role["id"]][permission["id"]]
            except KeyError:
                has_permission = False
            else:
                has_permission = True

            roles.append({
                "id": role["id"],
                "name": role["name"],
                "has_permission": has_permission,
            })

        my_permissions.append({
            "name": permission["name"],
            "codename": permission["codename"],
            "roles": roles,
        })

    return render_to_string(template_name, RequestContext(request, {
        "roles": all_roles,
        "permissions": my_permissions,
    }))


def update_portal_permissions(request):
    """Saves the portal permissions tab.

    **Permission:**

        manage_portal
    """
    portal = get_portal()
    portal.check_permission(request.user, "manage_portal")

    permissions_dict = dict()
    for permission in request.POST.getlist("permission"):
        permissions_dict[permission] = 1

    for role in Role.objects.all():
        for permission in Permission.objects.all():
            perm_string = "%s|%s" % (role.id, permission.codename)
            if perm_string in permissions_dict:
                portal.grant_permission(role, permission)
            else:
                portal.remove_permission(role, permission)

    html = (
        ("#permissions", portal_permissions(request, portal)),
    )

    result = json.dumps({
        "html": html,
        "message": _(u"Permissions have been saved."),
    }, cls=LazyEncoder)

    return HttpResponse(result)


def portal_tabs(request, portal, template_name="lfc/manage/portal_tabs.html"):
    """Displays the tabs of the portal management screen.

    **Parameters:**

        portal
            The portal for which the tabs should be displayed.

    **Permission:**

        None (as this is not called from outside)
    """
    if settings.LFC_MANAGE_PERMISSIONS:
        permissions = portal_permissions(request, portal)
    else:
        permissions = ""

    return render_to_string(template_name, RequestContext(request, {
        "core_data": portal_core(request, portal),
        "children": portal_children(request, portal),
        "portlets": portlets_inline(request, portal),
        "images": portal_images(request, portal),
        "files": portal_files(request, portal),
        "permissions": permissions,
    }))


def portal_menu(request, portal, template_name="lfc/manage/portal_menu.html"):
    """Displays the manage menu of the portal.

    **Parameters:**

        portal
            The portal for which the tabs should be displayed.

    **Permission:**

        None (as this is not called from outside)
    """
    content_types = get_allowed_subtypes()
    return render_to_string(template_name, RequestContext(request, {
        "display_paste": _display_paste(request, portal),
        "display_content_menu": len(content_types) > 1,
        "content_types": content_types,
    }))


def portal_core(request, portal=None, template_name="lfc/manage/portal_core.html"):
    """Displays the core data tab (GET) of the portal and saves it (POST).

    **Permissions:**

        * view (GET)
        * manage_portal (POST)
    """
    if portal is None:
        portal = lfc.utils.get_portal()

    if request.method == "POST":
        portal.check_permission(request.user, "manage_portal")
        form = PortalCoreForm(instance=portal, data=request.POST)
        if form.is_valid():
            message = _(u"Portal data has been saved.")
            form.save()
        else:
            message = _(u"An error has been occured.")

        html = render_to_string(template_name, RequestContext(request, {
            "form": form,
            "portal": portal,
        }))

        html = (
            ("#data", html),
        )

        result = json.dumps({
            "html": html,
            "message": message},
            cls=LazyEncoder
        )
        result = HttpResponse(result)
    else:
        portal.check_permission(request.user, "view")
        form = PortalCoreForm(instance=portal)

        result = render_to_string(template_name, RequestContext(request, {
            "form": form,
            "portal": portal,
        }))

    return result


def portal_children(request, portal, template_name="lfc/manage/portal_children.html"):
    """Displays the children tab of the portal.

    **Permission:**

        None (as this is not called from outside)
    """
    language = request.session.get("nav-tree-lang", settings.LANGUAGE_CODE)
    children = lfc.utils.get_content_objects(parent=None, language__in=("0", language))
    return render_to_string(template_name, RequestContext(request, {
        "children": children,
        "display_paste": _display_paste(request, portal),
    }))


def portal_images(request, portal, template_name="lfc/manage/portal_images.html"):
    """Displays the content of the images tab of the portal management screen.

    **Permission:**

        None (as this is not called from outside)
    """
    return render_to_string(template_name, RequestContext(request, {
        "obj": portal,
        "images": portal.images.all(),
    }))


def portal_files(request, portal, template_name="lfc/manage/portal_files.html"):
    """Displays the content of the files tab of the portal management screen.

    **Permission:**

        None (as this is not called from outside)
    """
    return render_to_string(template_name, RequestContext(request, {
        "obj": portal,
    }))


# actions
def update_portal_children(request):
    """Deletes/Updates the children of the portal with passed ids (via
    request body).

    **Permission:**

        manage_portal
    """
    portal = lfc.utils.get_portal()
    portal.check_permission(request.user, "manage_portal")

    message = _update_children(request, portal)

    html = (
        ("#children", portal_children(request, portal)),
        ("#navigation", navigation(request, None)),
        ("#menu", portal_menu(request, portal)),
    )

    result = json.dumps({
        "html": html,
        "message": message,
    }, cls=LazyEncoder)

    return HttpResponse(result)


def move_portal_child(request, child_id):
    """Moves the child with passed child

    **Parameters:**

        child_id
            The id of the obj which should be moved.

    **Query String:**

        direction
            The direction in which the child should be moved. One of 0 (up)
            or 1 (down).

    **Permission:**

        manage_portal
    """
    portal = lfc.utils.get_portal()
    portal.check_permission(request.user, "manage_portal")

    obj = lfc.utils.get_content_object(pk=child_id)

    direction = request.GET.get("direction", 0)

    if direction == "1":
        obj.position += 15
    else:
        obj.position -= 15
    obj.save()
    _update_positions(None)

    html = (
        ("#children", portal_children(request, portal)),
        ("#navigation", navigation(request, None)),
    )

    result = json.dumps({
        "html": html,
    }, cls=LazyEncoder)

    return HttpResponse(result)


def load_portal_images(request):
    """Loads the portal images tab after images have been uploaded.

    **Permission:**

        view
    """
    get_portal().check_permission(request.user, "view")

    return HttpJsonResponse(
        content=portal_images(request, get_portal()),
        message=_(u"Images have been added."),
        mimetype="text/plain",
    )


def update_portal_images(request):
    """Updates/Deletes images of the portal.

    **Query String:**

        action
            The action which should be performed. One of: delete, update

        delete-images
            A list of ids of the images which should be deleted. Used for
            delete action

        title-x
            The title of the image with id x. Used for update action.

        position-x
            The position of the image with id x. Used for update action.

        caption-x
            The title of the image with id x. Used for update action.

    **Permission:**

        manage_portal
    """
    portal = lfc.utils.get_portal()
    portal.check_permission(request.user, "manage_portal")

    message = _update_images(request, portal)

    return HttpJsonResponse(
        content=[["#images", portal_images(request, portal)]],
        message=message,
        mimetype="text/plain",
    )


def add_portal_images(request):
    """Adds images to the portal.

    **Permission:**

        manage_portal
    """
    user = lfc.utils.get_user_from_session_key(request.COOKIES.get("sessionid"))

    portal = lfc.utils.get_portal()
    portal.check_permission(user, "manage_portal")

    for file_content in request.FILES.getlist("file"):
        image = Image(content=portal, title=file_content.name)
        image.image.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, image in enumerate(portal.images.all()):
        image.position = (i + 1) * 10
        image.save()

    return HttpResponse("")


def move_image(request, id):
    """Moves the image with passed id up or down.

    **Parameters:**

        id
            The id of the image which should be edited.

    **Query String:**

        direction
            The direction in which the image should be moved. One of 0 (up)
            or 1 (down).

    **Permission:**

        edit (of the belonging content object)
    """
    image = Image.objects.get(pk=id)

    obj = image.content
    if obj is None:
        obj = lfc.utils.get_portal()

    obj.check_permission(request.user, "edit")

    direction = request.GET.get("direction", 0)

    if direction == "1":
        image.position += 15
    else:
        image.position -= 15
        if image.position < 0:
            image.position = 10

    image.save()

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = (i + 1) * 10
        image.save()

    if isinstance(obj, Portal):
        images = portal_images(request, obj)
    else:
        images = object_images(request, obj)

    return HttpJsonResponse(
        content=[["#images", images]],
        mimetype="text/plain",
    )


def edit_image(request, id):
    """Displays a form to edit the image with passed id.

    **Parameters:**

        id
            The id of the image which should be edited.

    **Permission:**

        edit (of the belonging content object)
    """
    image = Image.objects.get(pk=id)

    obj = image.content
    if obj is None:
        obj = lfc.utils.get_portal()
    obj.check_permission(request.user, "edit")

    if request.method == "GET":
        form = ImageForm(prefix="image", instance=image)
        html = render_to_string("lfc/manage/image.html", RequestContext(request, {
            "form": form,
            "image": image,
        }))

        return HttpJsonResponse(
            content=[["#overlay .content", html]],
            open_overlay=True,
            mimetype="text/plain",
        )
    else:
        form = ImageForm(prefix="image", instance=image, data=request.POST)
        if form.is_valid():
            image = form.save()
            images = object_images(request, image.content)

            return HttpJsonResponse(
                content=[["#images", images]],
                close_overlay=True,
                message=_(u"Image has been saved.")
            )
        else:
            html = render_to_string("lfc/manage/image.html", RequestContext(request, {
                "form": form,
                "image": image,
            }))

            return HttpJsonResponse(
                content=[["#overlay .content", html]],
                mimetype="text/plain",
            )


def add_portal_files(request):
    """Addes files to the portal.

    **Permission:**

        manage_portal
    """
    user = lfc.utils.get_user_from_session_key(request.COOKIES.get("sessionid"))

    portal = lfc.utils.get_portal()
    portal.check_permission(user, "manage_portal")

    for file_content in request.FILES.getlist("file"):
        file = File(content=portal, title=file_content.name)
        file.file.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, file in enumerate(portal.files.all()):
        file.position = (i + 1) * 10
        file.save()

    return HttpResponse("result")


def load_portal_files(request):
    """Loads the portal files tab after files have been uploaded.

    **Permission:**

        view
    """
    get_portal().check_permission(request.user, "view_management")
    get_portal().check_permission(request.user, "view")

    return HttpJsonResponse(
        content=portal_files(request, get_portal()),
        message=_(u"Files have been added."),
        mimetype="text/plain",
    )


def update_portal_files(request):
    """Saves/Deletes files for the portal.

    **Permission:**

        manage_portal
    """
    portal = lfc.utils.get_portal()
    portal.check_permission(request.user, "manage_portal")

    message = _update_files(request, portal)

    json = render_to_json(
        html=[["#files", portal_files(request, portal)]],
        message=message,
    )

    return HttpResponse(json)


def move_file(request, id):
    """Moves the image with passed id up or down.

    **Parameters:**

        id
            The id of the image which should be edited.

    **Query String:**

        direction
            The direction in which the image should be moved. One of 0 (up)
            or 1 (down).

    **Permission:**

        edit (of the belonging content object)
    """
    file = File.objects.get(pk=id)

    obj = file.content
    if obj is None:
        obj = lfc.utils.get_portal()

    obj.check_permission(request.user, "edit")

    direction = request.GET.get("direction", 0)

    if direction == "1":
        file.position += 15
    else:
        file.position -= 15
        if file.position < 0:
            file.position = 10

    file.save()

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = (i + 1) * 10
        file.save()

    if isinstance(obj, Portal):
        files = portal_files(request, obj)
    else:
        files = object_files(request, obj)

    return HttpJsonResponse(
        content=[["#files", files]],
        mimetype="text/plain",
    )


def edit_file(request, id):
    """Displays a edit form (GET) for a file and saves it (POST).

    **Parameters:**

        id
            The id of the file which should be edited.

    **Permission:**

        edit
    """
    file = File.objects.get(pk=id)
    file.content.check_permission(request.user, "edit")

    if request.method == "GET":
        form = FileForm(prefix="file", instance=file)

        html = render_to_string("lfc/manage/file.html", RequestContext(request, {
            "form": form,
            "file": file,
        }))

        return HttpJsonResponse(
            content=[["#overlay .content", html]],
            open_overlay=True,
            mimetype="text/plain",
        )
    else:
        form = FileForm(prefix="file", instance=file, data=request.POST)
        if form.is_valid():
            file = form.save()
            files = object_files(request, file.content)

            return HttpJsonResponse(
                content=[["#files", files]],
                close_overlay=True,
                message=_(u"File has been saved.")
            )
        else:
            html = render_to_string("lfc/manage/file.html", RequestContext(request, {
                "form": form,
                "file": file,
            }))

            return HttpJsonResponse(
                content=[["#overlay .content", html]],
                mimetype="text/plain",
            )


# Objects ####################################################################
##############################################################################
def manage_object(request, id, template_name="lfc/manage/object.html"):
    """Displays the main management screen with all tabs of the content object
    with passed id.

    **Parameters:**

        id
            The id of the object which should be displayed.

    **Permission:**

        view_management
    """
    try:
        obj = lfc.utils.get_content_object(pk=id)
    except BaseContent.DoesNotExist:
        url = reverse("lfc_manage_portal")
        return HttpResponseRedirect(url)

    obj.check_permission(request.user, "view_management")

    if not lfc.utils.registration.get_info(obj):
        raise Http404()

    result = render_to_string(template_name, RequestContext(request, {
        "navigation": navigation(request, obj),
        "menu": object_menu(request, obj),
        "tabs": object_tabs(request, obj),
        "obj": obj,
    }))

    return HttpResponse(result)


def object_menu(request, obj, template_name="lfc/manage/object_menu.html"):
    """Displays the manage menu for the passed object.

    **Parameters:**

        obj
            The current displayed object

    **Permission:**

        None (as this is not called from outside)
    """
    if obj.is_canonical():
        canonical = obj
    else:
        canonical = obj.canonical

    languages = []
    for language in settings.LANGUAGES:
        if language[0] != settings.LANGUAGE_CODE:
            languages.append({
                "code": language[0],
                "name": language[1],
            })

    if canonical:
        translations = canonical.translations.all()
    else:
        translations = None

    content_types = get_allowed_subtypes(obj)

    # Workflow
    transitions = obj.get_allowed_transitions(request.user)
    state = obj.get_state()

    return render_to_string(template_name, RequestContext(request, {
        "content_types": content_types,
        "display_content_menu": len(content_types) > 1,
        "display_action_menu": _display_action_menu(request, obj),
        "translations": translations,
        "languages": languages,
        "canonical": canonical,
        "obj": obj,
        "display_paste": _display_paste(request, obj),
        "transitions": transitions,
        "state": state,
    }))


def object_tabs(request, obj, template_name="lfc/manage/object_tabs.html"):
    """Displays the tabs for the passed object.

    **Parameters:**

        obj
            The content object for which the tabs should be displayed.

    **Permission:**

        None (as this is not called from outside)
    """
    if obj.has_meta_data_tab():
        meta_data = object_meta_data(request, obj)
    else:
        meta_data = None

    if obj.has_seo_tab():
        seo_data = object_seo_data(request, obj)
    else:
        seo_data = None

    if obj.has_images_tab():
        images = object_images(request, obj)
    else:
        images = None

    if obj.has_files_tab():
        files = object_files(request, obj)
    else:
        files = None

    if obj.has_comments_tab():
        object_comments = comments(request, obj)
    else:
        object_comments = None

    return render_to_string(template_name, RequestContext(request, {
        "obj": obj,
        "core_data": object_core_data(request, obj),
        "meta_data": meta_data,
        "seo_data": seo_data,
        "images": images,
        "files": files,
        "comments": object_comments,
        "content_type_name": get_info(obj).name,
        "tabs" : obj.get_tabs(request),
    }))


def object_core_data(request, obj=None, id=None, template_name="lfc/manage/object_data.html"):
    """Displays/Updates the core data tab of the content object with passed id.

    **Parameters:**

        obj
            The content object for which the core data should be displayed/
            updated.

    **Permission:**

        * edit (POST)
        * view (GET)
    """
    if obj is None:
        obj = lfc.utils.get_content_object(pk=id)

    Form = obj.edit_form

    if request.method == "POST":
        obj.check_permission(request.user, "edit")
        message = _("An error has been occured.")

        form = Form(instance=obj, data=request.POST)
        if form.is_valid():
            # Unfortunately this is not checked via the form is_valid method.
            try:
                BaseContent.objects.exclude(pk=id).get(slug=form.data.get("slug"), parent=obj.parent, language=obj.language)
            except BaseContent.DoesNotExist:
                form.save()
                message = _(u"Data has been saved.")
            else:
                form.errors["slug"] = _("An object with this slug already exists.")

        # We take the form from the db again in order to render the RichText
        # fielt correctly.
        # errors = form.errors
        # form = Form(instance=obj)
        # form._errors = errors
        data = render_to_string(template_name, RequestContext(request, {
            "form": form,
            "obj": obj,
        }))

        view_link = render_to_string("lfc/manage/object_view_link.html", RequestContext(request, {
            "obj": obj,
        }))

        quick_view_link = render_to_string("lfc/manage/object_quick_view_link.html", RequestContext(request, {
            "obj": obj,
        }))

        html = (
            ("#navigation", navigation(request, obj)),
            ("#object-view-link", view_link),
            ("#object-quick-view-link", quick_view_link),
            ("#core_data", data),
        )

        return HttpJsonResponse(
            content=html,
            message=message,
            mimetype="text/plain",
        )

    else:
        obj.check_permission(request.user, "view")
        form = Form(instance=obj)

        try:
            above_form = form.above_form(request)
        except AttributeError:
            above_form = ""

        try:
            below_form = form.below_form(request)
        except AttributeError:
            below_form = ""

        try:
            template_name = form.template_name
        except AttributeError:
            pass

        return render_to_string(template_name, RequestContext(request, {
            "form": form,
            "obj": obj,
            "above_form": above_form,
            "below_form": below_form,
        }))


def object_meta_data(request, obj=None, id=None, template_name="lfc/manage/object_meta_data.html"):
    """Displays/Updates the meta tab of the content object with passed id.

    **Parameters:**

        obj
            The content object for which the meta data should be displayed/
            updated.

    **Permission:**

        * edit (POST)
        * view (GET)
    """
    if obj is None:
        obj = lfc.utils.get_content_object(pk=id)
    if request.method == "POST":
        obj.check_permission(request.user, "edit")
        form = MetaDataForm(request=request, instance=obj, data=request.POST)
        if form.is_valid():

            if request.POST.get("start_date_0", "") == "" and request.POST.get("start_date_1", "") == "":
                obj.start_date = None
            if request.POST.get("end_date_0", "") == "" and request.POST.get("end_date_1", "") == "":
                obj.end_date = None
            if request.POST.get("publication_date_0", "") == "" and request.POST.get("publication_date_1", "") == "":
                obj.publication_date = None
            message = _(u"Meta data has been saved.")
            form.save()
            form = MetaDataForm(request=request, instance=_update_positions(obj, True))
        else:
            message = _(u"An error has been occured.")

        view_link = render_to_string("lfc/manage/object_view_link.html", RequestContext(request, {
            "obj": obj,
        }))

        quick_view_link = render_to_string("lfc/manage/object_quick_view_link.html", RequestContext(request, {
            "obj": obj,
        }))

        html = render_to_string(template_name, RequestContext(request, {
            "form": form,
            "obj": obj,
        }))

        html = (
            ("#meta_data", html),
            ("#navigation", navigation(request, obj)),
            ("#children", object_children(request, obj)),
            ("#object-view-link", view_link),
            ("#object-quick_view_link", quick_view_link),
        )

        return HttpJsonResponse(
            content=html,
            message=message,
            mimetype="text/plain",
        )

    else:
        obj.check_permission(request.user, "view")
        form = MetaDataForm(request=request, instance=obj)

        return render_to_string(template_name, RequestContext(request, {
            "form": form,
            "obj": obj,
        }))

def load_object_children(request, child_id):
    """Loads the object children tab per ajax.
    """
    obj = lfc.utils.get_content_object(pk=child_id)
    obj.check_permission(request.user, "view")
    return HttpResponse(object_children(request, obj))

def object_children(request, obj, template_name="lfc/manage/object_children.html"):
    """Displays the children tab of the passed content object.

    **Parameters:**

        obj
            The content object from which the children are displayed.
    """
    return render_to_string(template_name, RequestContext(request, {
        "obj": obj,
        "children": obj.get_children(request),
        "display_paste": _display_paste(request, obj),
        "display_positions" : obj.order_by.find("position") != -1,
    }))


def object_images(request, obj, template_name="lfc/manage/object_images.html"):
    """Displays the images tab of the passed content object.

    **Parameters:**

        obj
            The object from which the files should be displayed.
    """
    return render_to_string(template_name, RequestContext(request, {
        "obj": obj,
    }))


def object_files(request, obj, template_name="lfc/manage/object_files.html"):
    """Displays the files tab of the passed content object.

    **Parameters:**

        obj
            The obj for which the files should be displayed.
    """
    return render_to_string(template_name, RequestContext(request, {
        "obj": obj,
    }))


def object_seo_data(request, obj=None, id=None, template_name="lfc/manage/object_seo.html"):
    """Displays/Updates the SEO tab of the passed content object.

    **Parameters:**

        obj
            The content object for which the SEO data should be displayed/
            updated.

    **Permission:**

        * edit (POST)
        * view (GET)
    """
    if obj is None:
        obj = lfc.utils.get_content_object(pk=id)

    if request.method == "POST":
        obj.check_permission(request.user, "edit")

        form = SEOForm(instance=obj, data=request.POST)
        if form.is_valid():
            form.save()

        html = render_to_string(template_name, RequestContext(request, {
            "form": form,
            "obj": obj,
        }))

        html = (
            ("#seo", html),
        )
        result = json.dumps({
            "html": html,
            "message": _(u"SEO has been saved."),
        }, cls=LazyEncoder)

        return HttpResponse(result)
    else:
        obj.check_permission(request.user, "view")
        form = SEOForm(instance=obj)
        return render_to_string(template_name, RequestContext(request, {
            "form": form,
            "obj": obj,
        }))


def load_object_permissions(request, id):
    """Loads object_permissions via ajax.

    **Parameters:**

        id
            The id of the content object for which the permissions should be
            loaded

    **Permission:**

        view
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "view")
    return HttpResponse(object_permissions(request, obj))


def object_permissions(request, obj, template_name="lfc/manage/object_permissions.html"):
    """Displays the permissions tab of the passed content object.

    **Parameters:**

        obj
            The content object for which the permissions should be displayed

    **Permission:**

        None (as this is not called from outside)
    """
    base_ctype = ContentType.objects.get_for_model(BaseContent)
    ctype = ContentType.objects.get_for_model(obj)

    permissions_dict = {}
    for op in ObjectPermission.objects.filter(content_type=ctype, content_id=obj.id).values("role_id", "permission_id"):
        role_id = op["role_id"]
        permission_id = op["permission_id"]
        if not permissions_dict.has_key(role_id):
            permissions_dict[role_id] = {}
        permissions_dict[role_id][permission_id] = 1
    all_roles = Role.objects.all().values("id", "name")

    # Get permissions which are managed by current workflow
    workflow = obj.get_workflow()
    if workflow:
        wf_permissions = [p["id"] for p in workflow.permissions.values("id")]
    else:
        wf_permissions = []

    q = Q(content_types__in=(ctype, base_ctype)) | Q(content_types=None)
    my_permissions = []
    for permission in Permission.objects.filter(q).order_by("name").values("id", "name", "codename"):
        roles = []
        for role in all_roles:
            try:
                permissions_dict[role["id"]][permission["id"]]
            except KeyError:
                has_permission = False
            else:
                has_permission = True

            roles.append({
                "id": role["id"],
                "name": role["name"],
                "has_permission": has_permission,
            })

        # Find out whether the permission is inherited or not
        try:
            ObjectPermissionInheritanceBlock.objects.get(
                content_type=ctype, content_id=obj.id, permission__codename = permission["codename"])
        except ObjectDoesNotExist:
            is_inherited = True
        else:
            is_inherited = False

        my_permissions.append({
            "name": permission["name"],
            "codename": permission["codename"],
            "roles": roles,
            "is_inherited": is_inherited,
            "is_wf_permission": permission["id"] in wf_permissions,
        })

    return render_to_string(template_name, RequestContext(request, {
        "obj": obj,
        "roles": all_roles,
        "permissions": my_permissions,
        "workflow": workflow,
        "local_roles": local_roles(request, obj),
    }))


def local_roles(request, obj, template_name="lfc/manage/local_roles.html"):
    """Displays local roles of the passed content object.

    **Parameters:**

        obj
            The content object for which the local roles are displayed.

    **Permission:**

        None (as this is not called from outside)
    """
    all_roles = Role.objects.all()
    ctype = ContentType.objects.get_for_model(obj)

    temp = []
    users = []
    for user in [prr.user for prr in PrincipalRoleRelation.objects.exclude(user=None).filter(content_id=obj.id, content_type=ctype)]:

        # Every user just one time
        if user.id in temp:
            continue
        temp.append(user.id)

        local_roles = obj.get_roles(user)
        roles = []
        for role in all_roles:
            roles.append({
                "id": role.id,
                "name": role.name,
                "has_local_role": role in local_roles,
            })

        if user.first_name and user.last_name:
            name = "%s %s" % (user.first_name, user.last_name)
        else:
            name = user.username

        users.append({
            "id": user.id,
            "name": name,
            "roles": roles,
        })

    temp = []
    groups = []
    for group in [prr.group for prr in PrincipalRoleRelation.objects.exclude(group=None).filter(content_id=obj.id, content_type=ctype)]:

        # Every group just one time
        if group.id in temp:
            continue
        temp.append(group.id)

        local_roles = obj.get_roles(group)
        roles = []
        for role in all_roles:
            roles.append({
                "id": role.id,
                "name": role.name,
                "has_local_role": role in local_roles,
            })

        groups.append({
            "id": group.id,
            "name": group.name,
            "roles": roles,
        })

    return render_to_string(template_name, RequestContext(request, {
        "users": users,
        "groups": groups,
        "roles": Role.objects.all(),
        "obj": obj,
    }))


def local_roles_add_form(request, id, template_name="lfc/manage/local_roles_add.html"):
    """Displays a form to add local roles to object with passed id.

    **Parameters:**

        id
            The id of the content object for which the form should be displayed.

    **Permission:**

        manage_local_roles
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "manage_local_roles")

    form = render_to_string(template_name, RequestContext(request, {
        "obj_id": id,
    }))

    json = render_to_json(
        html=[["#overlay .content", form]],
        open_overlay=True,
    )

    return HttpResponse(json)


def local_roles_search(request, id, template_name="lfc/manage/local_roles_search_result.html"):
    """Displays search results for local roles.

    **Parameters:**

        id
            The id of the content object for which the form should be displayed.

    **Permission:**

        manage_local_roles
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "manage_local_roles")

    ctype = ContentType.objects.get_for_model(obj)

    name = request.GET.get("name", "")
    q_users = Q(username__icontains=name) | Q(first_name__icontains=name) | Q(last_name__icontains=name)

    user_ids = [prr.user.id for prr in PrincipalRoleRelation.objects.exclude(user=None).filter(content_id=obj.id, content_type=ctype)]
    group_ids = [prr.group.id for prr in PrincipalRoleRelation.objects.exclude(group=None).filter(content_id=obj.id, content_type=ctype)]

    html = render_to_string(template_name, RequestContext(request, {
        "users": User.objects.exclude(pk__in=user_ids).filter(q_users),
        "groups": Group.objects.exclude(pk__in=group_ids).filter(name__icontains=name),
        "obj_id": id,
        "roles": Role.objects.exclude(name__in=("Anonymous", )),
    }))

    html = (
        ("#local-roles-search-result", html),
    )

    result = json.dumps({
        "html": html,
    }, cls=LazyEncoder)

    return HttpResponse(result)


# actions
def add_local_roles(request, id):
    """Add local roles the the object with passed id.

    **Parameters:**

        id
            The id of the content object to which the local roles should be
            added.

    **Query String:**

        user_role
            List of user/roles pair which should be added to the content object.

        group_role
            List of group/roles pair which should be added to the content
            object.

    **Permission:**

        manage_local_roles
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "manage_local_roles")

    for user_role in request.POST.getlist("user_role"):
        user_id, role_id = user_role.split("|")
        user = permissions.utils.get_user(user_id)
        role = permissions.utils.get_role(role_id)

        if user and role:
            obj.add_role(user, role)

    for group_role in request.POST.getlist("group_role"):
        group_id, role_id = group_role.split("|")
        group = permissions.utils.get_group(group_id)
        role = permissions.utils.get_role(role_id)

        if group and role:
            obj.add_role(group, role)

    message = _(u"Local roles has been added")

    html = (
        ("#local-roles", local_roles(request, obj)),
    )

    result = json.dumps({
        "html": html,
        "message": message,
    }, cls=LazyEncoder)

    return HttpResponse(result)


def save_local_roles(request, id):
    """Saves/Deletes local roles for the object with passed id.

    This is called from the permission tab of a content object.

    **Parameters:**

        id
            The id of the content object for which the local roles should be
            saved.

    **Query String:**

        action
            The action which should be performed. One of: deleted (delete
            selected users) or save (save selected user/role pairs)

        to_delete_user
            List of user ids which should be removed (for delete action)

        to_delete_group
            List of group ids which should be removed (for delete action)
            object.

        user_role
            List of user/role pairs (for save action)

        group_role
            List of group/role pairs (for save action)

    **Permission:**

        manage_local_roles
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "manage_local_roles")

    ctype = ContentType.objects.get_for_model(obj)

    if request.POST.get("action") == "delete":
        message = _(u"Local roles has been deleted")

        # Remove local roles for checked users
        for user_id in request.POST.getlist("to_delete_user"):
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                continue
            else:
                obj.remove_roles(user)

        # Remove local roles for checked groups
        for group_id in request.POST.getlist("to_delete_group"):
            try:
                group = Group.objects.get(pk=group_id)
            except Group.DoesNotExist:
                continue
            else:
                obj.remove_roles(group)
    else:
        message = _(u"Local roles has been saved")
        users_roles = request.POST.getlist("user_role")
        groups_roles = request.POST.getlist("group_role")

        temp = []
        for user in [prr.user for prr in PrincipalRoleRelation.objects.exclude(user=None).filter(content_id=obj.id, content_type=ctype)]:

            # Every user just one time
            if user.id in temp:
                continue
            temp.append(user.id)

            for role in Role.objects.all():
                if "%s|%s" % (user.id, role.id) in users_roles:
                    obj.add_role(user, role)
                else:
                    obj.remove_role(user, role)

        temp = []
        for group in [prr.group for prr in PrincipalRoleRelation.objects.exclude(group=None).filter(content_id=obj.id, content_type=ctype)]:

            # Every user just one time
            if group.id in temp:
                continue
            temp.append(group.id)

            for role in Role.objects.all():
                if "%s|%s" % (group.id, role.id) in groups_roles:
                    obj.add_role(group, role)
                else:
                    obj.remove_role(group, role)

    html = (
        ("#local-roles", local_roles(request, obj)),
    )

    result = json.dumps({
        "html": html,
        "message": message,
    }, cls=LazyEncoder)

    return HttpResponse(result)


def update_object_children(request, id):
    """Deletes/Updates children for the content object with the passed id.

    **Parameters:**

        id
            The id of the object for which the images should be deleted.

    **Query String:**

        action
            The action which should be performed. One of: delete, copy, cut,
            paste

    **Permission:**

        edit
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "edit")

    message = _update_children(request, obj)

    _update_positions(obj)

    html = (
        ("#navigation", navigation(request, obj.get_content_object())),
        ("#children", object_children(request, obj)),
        ("#menu", object_menu(request, obj)),
    )

    result = json.dumps({
        "html": html,
        "message": message,
    }, cls=LazyEncoder)

    return HttpResponse(result)


def move_object_child(request, child_id):
    """Moves the child with passed child

    **Parameters:**

        child_id
            The id of the obj which should be moved.

    **Query String:**

        direction
            The direction in which the child should be moved. One of 0 (up)
            or 1 (down).

    **Permission:**

        edit
    """
    obj = lfc.utils.get_content_object(pk=child_id)

    parent = obj.parent
    parent.check_permission(request.user, "edit")

    direction = request.GET.get("direction", 0)

    if direction == "1":
        obj.position += 15
    else:
        obj.position -= 15
    obj.save()
    _update_positions(parent)

    html = (
        ("#children", object_children(request, parent)),
        ("#navigation", navigation(request, parent.get_content_object())),
    )

    result = json.dumps({
        "html": html,
    }, cls=LazyEncoder)

    return HttpResponse(result)


def load_object_images(request, id):
    """Loads the portal images tab after images have been uploaded.

    **Permission:**

        view
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "view")

    return HttpJsonResponse(
        content=object_images(request, obj),
        message=_(u"Images have been added."),
        mimetype="text/plain",
    )


def add_object_images(request, id):
    """Adds images to the object with the given id.

    The to be added images are passed within request.FILES.

    **Parameters:**

        id
            The id of the object for which the images should be deleted.

    **Permission:**

        edit
    """
    user = lfc.utils.get_user_from_session_key(request.COOKIES.get("sessionid"))
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(user, "edit")

    if request.method == "POST":
        for file_content in request.FILES.getlist("file"):
            image = Image(content=obj, title=file_content.name)
            image.image.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = (i + 1) * 10
        image.save()

    lfc.utils.clear_cache()

    files = []
    files.append({
        "name": "hurz"
    })

    result = json.dumps({
        "files": files
    }, cls=LazyEncoder)

    return HttpResponse(result)


def update_object_images(request, id):
    """Saves/deletes images for content object with passed id.

    **Parameters:**

        id
            The id of the object for which the images should be deleted.

    **Query String:**

        action
            The action which should be performed. One of: delete, update

        delete-images
            A list of ids of the images which should be deleted. Used for
            delete action

        title-x
            The title of the image with id x. Used for update action.

        position-x
            The position of the image with id x. Used for update action.

        caption-x
            The title of the image with id x. Used for update action.

    **Permission:**

            edit
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "edit")

    message = _update_images(request, obj)
    lfc.utils.clear_cache()

    json = render_to_json(
        html=[["#images", object_images(request, obj)]],
        message=message,
    )

    return HttpResponse(json)


def load_object_files(request, id):
    """Loads the portal files tab after files have been uploaded.

    **Permission:**

        view
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "view")

    return HttpJsonResponse(
        content=object_files(request, obj),
        message=_(u"Files have been added."),
        mimetype="text/plain",
    )


def add_object_files(request, id):
    """Adds images to the object with the given id.

    The to be added images are passed within request.FILES.

    **Parameters:**

        id
            The id of the object for which the images should be deleted.

    **Permission:**

        edit
    """
    user = lfc.utils.get_user_from_session_key(request.COOKIES.get("sessionid"))
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(user, "edit")

    if request.method == "POST":
        for file_content in request.FILES.getlist("file"):
            file = File(content=obj, title=file_content.name)
            file.file.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = (i + 1) * 10
        file.save()

    return HttpResponse("")


def update_object_files(request, id):
    """Saves/deletes files for the content object with the passed id.

    **Parameters:**

        id
            The content object for which the files are updated.

    **Permission:**

        edit
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "edit")

    message = _update_files(request, obj)

    json = render_to_json(
        html=[["#files", object_files(request, obj)]],
        message=message,
    )

    return HttpResponse(json)


def update_object_permissions(request, id):
    """Updates the permissions for the object with passed id.

    **Parameters:**

        id
            The content object for which the files are updated.

    **Permission:**

        edit
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "edit")

    permissions_dict = dict()
    for permission in request.POST.getlist("permission"):
        permissions_dict[permission] = 1

    q = Q(content_types=obj) | Q(content_types=None)

    for role in Role.objects.all():
        for permission in Permission.objects.filter(q):
            perm_string = "%s|%s" % (role.id, permission.codename)
            if perm_string in permissions_dict:
                obj.grant_permission(role, permission)
            else:
                obj.remove_permission(role, permission)

    inheritance_dict = dict()
    for permission in request.POST.getlist("inherit"):
        inheritance_dict[permission] = 1

    for permission in Permission.objects.filter(q):
        if permission.codename in inheritance_dict:
            obj.remove_inheritance_block(permission)
        else:
            obj.add_inheritance_block(permission)

    html = (
        ("#permissions", object_permissions(request, obj)),
    )

    result = json.dumps({
        "html": html,
        "message": _(u"Permissions have been saved."),
    }, cls=LazyEncoder)

    return HttpResponse(result)


# Portlets ###################################################################
##############################################################################


def load_object_portlets(request, id):
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "view")
    return HttpResponse(portlets_inline(request, obj))


def portlets_inline(request, obj, template_name="lfc/manage/portlets_inline.html"):
    """Displays the assigned portlets for given object.

    **Parameters:**

        obj
            The content object for which the portlets are displayed.
    """
    ct = ContentType.objects.get_for_model(obj)

    parent_for_portlets = obj.get_parent_for_portlets()
    if parent_for_portlets:
        parent_slots = get_slots(parent_for_portlets)
    else:
        parent_slots = None

    if obj.content_type == "portal":
        display_edit = obj.has_permission(request.user, "manage_portal")
    else:
        display_edit = obj.has_permission(request.user, "edit")

    return render_to_string(template_name, RequestContext(request, {
        "slots": get_slots(obj),
        "parent_slots": parent_slots,
        "parent_for_portlets": parent_for_portlets,
        "portlet_types": PortletRegistration.objects.all(),
        "obj": obj,
        "object_type_id": ct.id,
        "display_edit": display_edit,
    }))


# TODO: Remove object_type_id
def update_portlets_blocking(request, object_type_id, object_id):
    """Updates portlets blocking.

    **Parameters:**

        object_type_id
            The id of the type of the object for which the portlets should be
            updated (this might removed in future).

        object_id
            The id of the object for which the portlets should be updated.

    **Permission:**

        edit
    """
    # Get content type
    object_ct = ContentType.objects.get(pk=object_type_id)
    obj = object_ct.get_object_for_this_type(pk=object_id)
    obj.check_permission(request.user, "edit")

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

    html = (
        ("#portlets", portlets_inline(request, obj)),
    )

    result = json.dumps({
        "html": html,
        "message": _(u"Portlets have been updated.")},
        cls=LazyEncoder
    )
    return HttpResponse(result)


# TODO: Remove object_type_id
def add_portlet(request, object_type_id, object_id, template_name="lfc/manage/portlet_add.html"):
    """Displays a form to add a new portlet (GET) and adds them to the object
    with passed type and id (POST).

    **Parameters:**

        object_type_id
            The id of the type of the object for which the portlets should be
            updated (this might removed in future).

        object_id
            The id of the object for which the portlets should be updated.

    **Permission:**

        edit
    """
    # Get content type to which the portlet should be added
    object_ct = ContentType.objects.get(pk=object_type_id)
    obj = object_ct.get_object_for_this_type(pk=object_id)
    obj.check_permission(request.user, "edit")

    # Get the portlet type
    portlet_type = request.REQUEST.get("portlet_type", "")

    if request.method == "GET":
        try:
            portlet_ct = ContentType.objects.filter(model=portlet_type.lower())[0]
            mc = portlet_ct.model_class()
            form = mc().form(prefix="portlet")
            form = render_to_string(template_name, RequestContext(request, {
                "form": form,
                "object_id": object_id,
                "object_type_id": object_ct.id,
                "portlet_type": portlet_type,
                "slots": Slot.objects.all(),
            }))

            html = (("#overlay .content", form),)
            return HttpResponse(render_to_json(html=html, open_overlay=True))

        except ContentType.DoesNotExist:
            pass
    else:
        try:
            ct = ContentType.objects.filter(model=portlet_type.lower())[0]
            mc = ct.model_class()
            form = mc().form(prefix="portlet", data=request.POST)

            if form.is_valid():
                portlet = form.save()

                slot_id = request.POST.get("slot")
                position = request.POST.get("position", 999)
                pa = PortletAssignment.objects.create(
                    slot_id=slot_id, content=obj, portlet=portlet, position=position)

                html = portlets_inline(request, obj)
                response = render_to_json(
                    html=[["#portlets", html]],
                    message=_(u"Portlet has been added."),
                    success=True,
                    close_overlay=True,
                )

                lfc.utils.clear_cache()
                update_portlet_positions(pa)
            else:
                html = render_to_string(template_name, RequestContext(request, {
                    "form": form,
                    "object_id": object_id,
                    "object_type_id": object_ct.id,
                    "portlet_type": portlet_type,
                    "slots": Slot.objects.all(),
                }))
                response = render_to_json(
                    html=[["#overlay .content", html]],
                    message=_(u"An error has been occured."),
                    success=False,
                )

            return HttpResponse(response)

        except ContentType.DoesNotExist:
            pass


def delete_portlet(request, portletassignment_id):
    """Deletes a portlet for passed portlet assignment.

    **Parameters:**

        portletassignment_id
            ID of the PortletAssignment which should be deleted.

    **Permission:**

        edit
    """
    try:
        pa = PortletAssignment.objects.get(pk=portletassignment_id)
        pa.content.check_permission(request.user, "edit")
    except PortletAssignment.DoesNotExist:
        pass
    else:
        pa.portlet.delete()
        pa.delete()
        lfc.utils.clear_cache()
        update_portlet_positions(pa)

        html = (
            ("#portlets", portlets_inline(request, pa.content)),
        )

        return return_as_json(html, _(u"Portlet has been deleted."))


def edit_portlet(request, portletassignment_id, template_name="lfc/manage/portlet_edit.html"):
    """Displays a form to edit a portlet (GET) and saves it (POST).

    **Parameters:**

        portletassignment_id
            ID of the PortletAssignment which should be deleted.

    **Permission:**

        edit
    """
    try:
        pa = PortletAssignment.objects.get(pk=portletassignment_id)
        pa.content.check_permission(request.user, "edit")

    except PortletAssignment.DoesNotExist:
        return ""

    slots = []
    for slot in Slot.objects.all():
        slots.append({
            "id": slot.id,
            "name": slot.name,
            "selected": slot.id == pa.slot.id,
        })

    if request.method == "GET":

        form = pa.portlet.form(prefix="portlet")

        html = render_to_string(template_name, RequestContext(request, {
            "form": form,
            "portletassigment_id": pa.id,
            "slots": slots,
            "position": pa.position,
        }))

        return HttpResponse(render_to_json(
            html=[["#overlay .content", html]],
            open_overlay=True,
        ))

    else:
        form = pa.portlet.form(prefix="portlet", data=request.POST)

        if form.is_valid():
            form.save()

            # Save the rest
            pa.slot_id = request.POST.get("slot")
            pa.save()
            lfc.utils.clear_cache()
            update_portlet_positions(pa)

            html = portlets_inline(request, pa.content)

            response = render_to_json(
                html=[["#portlets", html]],
                message=_(u"Portlet has been saved."),
                success=True,
                close_overlay=True,
            )
        else:

            html = render_to_string(template_name, RequestContext(request, {
                "form": form,
                "portletassigment_id": pa.id,
                "slots": slots,
                "position": pa.position,
            }))

            response = json.dumps({
                "html": html,
                "message": _(u"An error has been occured."),
                "success": False},
                cls=LazyEncoder
            )

        return HttpResponse(response)


def move_portlet(request, portletassignment_id):
    """Moves a portlet up/down within a slot.

    **Parameters:**

        portletassignment_id
            The portlet assignment (hence the portlet) which should be moved.

    **Query String:**

        direction
            The direction to which the portlet should be moved. One of 0 (up)
            or 1 (down).

    **Permission:**

        edit
    """
    try:
        pa = PortletAssignment.objects.get(pk=portletassignment_id)
        pa.content.check_permission(request.user, "edit")
    except PortletAssignment.DoesNotExist:
        return ""

    direction = request.GET.get("direction", "0")
    if direction == "1":
        pa.position += 15
    else:
        pa.position -= 15
        if pa.position < 0:
            pa.position = 10
    pa.save()
    update_portlet_positions(pa)

    html = (
        ("#portlets", portlets_inline(request, pa.content)),
    )

    result = render_to_json(html)
    return HttpResponse(result)


def update_portlet_positions(pa):
    """Updates the portlet positions for a content object and a slot.

    **Parameters:**

        pa
            PortletAssignment which contains the slot and the content object
            in question.

    **Permission:**

        None (as this is not called from outside)
    """
    for i, pa in enumerate(PortletAssignment.objects.filter(content_type=pa.content_type, content_id=pa.content_id, slot=pa.slot)):
        pa.position = (i + 1) * 10
        pa.save()


# Navigation tree ############################################################
##############################################################################
def navigation(request, obj, start_level=1, template_name="lfc/manage/navigation.html"):
    """Displays the navigation tree of the management interfaces.

    **Parameters:**

        obj
            The current displayed content object. If this is None the Portal
            is the current object.

        start_level
            The start level of the navigation tree.

    **Permission:**

        None (as this is not called from outside)
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
    q = Q(parent=None) & Q(language__in=("0", nav_tree_lang))

    temps = lfc.utils.get_content_objects(request, q)

    objs = []
    for temp in temps:
        temp = temp.get_content_object()

        if not temp.has_permission(request.user, "view"):
            continue

        if temp in current_objs:
            children = _navigation_children(request, current_objs, temp, start_level)
            is_current = True
        else:
            children = ""
            is_current = False

        objs.append({
            "id": temp.id,
            "title": temp.title,
            "is_current": is_current,
            "children": children,
            "level": 2,
            "translations": temp.translations.all(),
        })

    languages = []
    for language in settings.LANGUAGES:
        if nav_tree_lang == language[0]:
            current_language = language[1]
        languages.append({
            "code": language[0],
            "name": language[1],
        })

    return render_to_string(template_name, RequestContext(request, {
        "obj": obj,
        "objs": objs,
        "show_level": start_level == 2,
        "level": 2,
        "languages": languages,
        "current_language": current_language,
        "is_portal": is_portal,
    }))


def _navigation_children(request, current_objs, obj, start_level, level=3):
    """Renders the children of the given object (recursively).

    **Parameters:**

        current_objs
            A list of current_objs

        obj
            The object for which the children should be rendered.

        start_level
            The start level of the navigation tree.

        level
            The current level of the navigation tree.
    """
    obj = obj.get_content_object()
    temp = obj.get_children(request)

    objs = []
    for obj in temp:
        obj = obj.get_content_object()

        if not lfc.utils.registration.get_info(obj):
            continue

        if obj in current_objs:
            children = _navigation_children(request, current_objs, obj, start_level, level + 1)
            is_current = True
        else:
            children = ""
            is_current = False

        objs.append({
            "id": obj.id,
            "title": obj.title,
            "is_current": is_current,
            "children": children,
            "level": level,
        })

    result = render_to_string("lfc/manage/navigation_children.html", {
        "objs": objs,
        "show_level": level >= start_level,
        "level": level,
    })

    return result


# PERMISSION: check which permission is needed.
@login_required
def set_navigation_tree_language(request, language):
    """Sets the language for the navigation tree.

    **Parameters:**

        language
            The language which should be set. Must be a two digit country code,
            e.g. en or de.

    **Query String:**

        id
            The id of the current displayed object.

    **Permission:**

        login_required (This need to be checked).

    """
    id = request.REQUEST.get("id")
    if id:
        obj = lfc.utils.get_content_object(pk=id)
    else:
        obj = None

    request.session["nav-tree-lang"] = language

    html = (
        ("#navigation", navigation(request, obj)),
    )

    return return_as_json(html, _(u"Tree language has been changed."))


@login_required
def set_language(request, language):
    """Sets the language of the portal.

    **Parameters:**

        language
            The language which should be set. Must be a two digit country code,
            e.g. en or de.

    **Permission:**

        login_required (This need to be checked).
    """
    translation.activate(language)
    response = HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    if translation.check_for_language(language):
        if hasattr(request, 'session'):
            request.session['django_language'] = language
        else:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)

    return response


# Comments ###################################################################
##############################################################################
def comments(request, obj, template_name="lfc/manage/object_comments.html"):
    """Displays the comments tab of the passed object.

    **Parameters:**

        obj
            The object for which the comments should be displayed.

    **Permission:**

        None (as this is not called from outside)
    """
    form = CommentsForm(instance=obj)
    comments = Comment.objects.filter(object_pk=str(obj.id))

    return render_to_string(template_name, RequestContext(request, {
        "obj": obj,
        "comments": comments,
        "form": form,
    }))


def update_comments(request, id):
    """Deletes/Updates comments from the object with passed id. The to updated
    comment ids are passed passed by request body.

    **Parameters:**

        id
            The id of the object for which the comments should be updated.

    **Permission:**

        edit
    """
    obj = get_object_or_404(BaseContent, pk=id)
    obj.check_permission(request.user, "edit")

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

    result = json.dumps({
        "html": html,
        "message": message,
    }, cls=LazyEncoder)

    return HttpResponse(result)


def edit_comment(request, id, template_name="lfc/manage/comment.html"):
    """Provides a form to edit a comment and saves it.

    **Parameters:**

        id
            The id of the comment which should be edited.

    **Permission:**

        edit (of the belonging content object)
    """
    comment = Comment.objects.get(pk=id)

    obj = comment.content_object
    obj.check_permission(request.user, "edit")

    if request.method == "GET":
        form = CommentForm(instance=comment)

        html = render_to_string("lfc/manage/comment.html", RequestContext(request, {
            "form": form,
            "comment": comment,
        }))

        return HttpJsonResponse(
            content=[["#overlay .content", html]],
            open_overlay=True,
            mimetype="text/plain",
        )
    else:
        form = CommentForm(instance=comment, data=request.POST)
        if form.is_valid():
            comment = form.save()
            html = comments(request, obj)

            return HttpJsonResponse(
                content=[["#comments", html]],
                close_overlay=True,
                message=_(u"Comment has been saved.")
            )
        else:
            html = render_to_string("lfc/manage/comment.html", RequestContext(request, {
                "form": form,
                "comment": comment,
            }))

            return HttpJsonResponse(
                content=[["#overlay .content", html]],
                mimetype="text/plain",
            )


# Filebrowser ################################################################
##############################################################################
def imagebrowser(request, obj_id=None, as_string=False, template_name="lfc/manage/filebrowser_images.html"):
    """Displays a browser for images.

    **Parameters:**

        obj_id
            The current displayed object.

        as_string
            If True the rendered HTML will be returned as string. Otherwise
            as HttpResponse.

    **Query String:**

        current_id
            The current displayed object.

    **Permission:**

        edit
    """
    obj_id = request.GET.get("obj_id", obj_id)
    url = request.GET.get("url")
    selected_class = request.GET.get("class")
    current_id = request.GET.get("current_id", obj_id)
    current_obj = lfc.utils.get_content_object(pk=current_id)

    selected_size = None
    selected_image = None
    portal = get_portal()

    if url:
        parsed_url = urlparse.urlparse(url)
        try:
            temp_url = "/".join(parsed_url.path.split("/")[2:])
            result = re.search("(.*)(\.)(\d+x\d+)(.*)", temp_url)
            temp_url = result.groups()[0] + result.groups()[3]
            selected_image = Image.objects.get(
                image=temp_url)
            obj = selected_image.content
            temp = obj
            is_portal = False
            selected_size = result.groups()[2]
        except (IndexError, Image.DoesNotExist):
            pass
    else:
        try:
            obj = lfc.utils.get_content_object(pk=obj_id)
            temp = obj
            is_portal = False
        except (BaseContent.DoesNotExist, ValueError):
            temp = None
            is_portal = True
            obj = portal

    obj.check_permission(request.user, "edit")

    objs = []
    while temp is not None:
        objs.insert(0, temp)
        temp = temp.parent

    children = []
    for child in obj.get_children(request):
        display = []
        if child.has_children(request):
            display.append(u"C")
        if child.images.count():
            display.append(u"I")

        display = "|".join(display)

        if display:
            display = "[%s]" % display

        children.append({
            "id": child.id,
            "title": child.title,
            "display": display,
        })

    images = []
    for image in obj.images.all():
        images.append({
            "id": image.id,
            "title": image.title,
            "checked": image == selected_image,
            "url": image.image.url_200x200,
        })

    sizes = []
    for size in IMAGE_SIZES:
        size = "%sx%s" % (size[0], size[1])
        sizes.append({
            "value": size,
            "title": size,
            "selected": size == selected_size,
        })

    classes = []
    for klass in ("inline", "left", "right"):
        classes.append({
            "value": klass,
            "title": klass,
            "selected": klass == selected_class,
        })
    html = render_to_string(template_name, RequestContext(request, {
        "portal": portal,
        "obj": obj,
        "obj_id": obj_id,
        "objs": objs,
        "children": children,
        "images": images,
        "current_id": current_id,
        "current_obj": current_obj,
        "display_upload": is_portal or obj_id,
        "sizes": sizes,
        "classes": classes,
        "selected_image": selected_image,
    }))

    if as_string:
        return html

    return HttpJsonResponse(
        content=html,
        mimetype="text/plain",
    )


def filebrowser(request, obj_id=None, as_string=False, template_name="lfc/manage/filebrowser_files.html"):
    """Displays a file browser.

    **Parameters:**

        obj_id
            The current displayed object.

        as_string
            If True the rendered HTML will be returned as string. Otherwise
            as HttpResponse.

    **Query String:**

        current_id
            The current displayed object.

    **Permission:**

        edit
    """
    obj_id = request.GET.get("obj_id", obj_id)

    # current_obj is the initial object which calls the filebrowser
    current_id = request.GET.get("current_id", obj_id)
    current_obj = lfc.utils.get_content_object(pk=current_id)

    portal = get_portal()

    obj = None
    url = request.GET.get("url")
    external_url = ""
    mail_url = ""

    selected_image = None
    selected_file = None
    selected_obj = None

    current_view = "content"

    if url:
        parsed_url = urlparse.urlparse(url)
        if parsed_url.scheme == "mailto":
            mail_url = parsed_url.path
            current_view = "mail"
        elif parsed_url.netloc == "localhost:8000":
            current_view = "content"
            if parsed_url.path.startswith("/file"):
                try:
                    id = parsed_url.path.split("/")[-1]
                    selected_file = File.objects.get(pk=id)
                    selected_obj = selected_file.content
                except (IndexError, Image.DoesNotExist):
                    pass
                temp = obj = selected_obj
                is_portal = False
            elif parsed_url.path.startswith("/media/uploads"):
                try:
                    selected_image = Image.objects.get(
                        image="/".join(parsed_url.path.split("/")[2:]))
                    selected_obj = selected_image.content
                except (IndexError, Image.DoesNotExist):
                    pass
                temp = obj = selected_obj
                is_portal = False
            else:
                try:
                    if selected_obj is None:
                        selected_obj = lfc.utils.traverse_object(request, parsed_url.path[1:])
                except Http404:
                    selected_obj = None
                else:
                    if selected_obj.parent:
                        temp = obj = selected_obj.parent
                        is_portal = False
                    else:
                        temp = None
                        is_portal = True
                        obj = portal
        else:
            external_url = parsed_url.netloc + parsed_url.path
            current_view = "extern"

    if obj is None:
        selected_obj = None
        try:
            obj = lfc.utils.get_content_object(pk=obj_id)
            temp = obj
            is_portal = False
        except (BaseContent.DoesNotExist, ValueError):
            temp = None
            is_portal = True
            obj = portal

    obj.check_permission(request.user, "edit")

    objs = []
    while temp is not None:
        objs.insert(0, temp)
        temp = temp.parent

    children = []
    for child in obj.get_children(request):

        display = []
        if child.has_children(request):
            display.append(u"C")
        if child.images.count():
            display.append(u"I")
        if child.files.count():
            display.append(u"F")
        display = "|".join(display)

        if display:
            display = "[%s]" % display

        children.append({
            "id": child.id,
            "title": child.title,
            "display": display,
            "url": child.get_absolute_url(),
            "checked": child == selected_obj,
        })

    files = []
    for file in obj.files.all():
        files.append({
            "id": file.id,
            "title": file.title,
            "checked": file == selected_file,
            "url": file.get_absolute_url(),
        })

    images = []
    for image in obj.images.all():
        images.append({
            "id": image.id,
            "title": image.title,
            "checked": image == selected_image,
            "url": image.image.url,
        })

    html = render_to_string(template_name, RequestContext(request, {
        "portal": portal,
        "obj": obj,
        "obj_id": obj_id,
        "objs": objs,
        "children": children,
        "files": files,
        "images": images,
        "current_id": current_id,
        "current_obj": current_obj,
        "display_upload": is_portal or obj_id,
        "title": request.GET.get("title", ""),
        "target": request.GET.get("target"),
        "external_url": external_url,
        "mail_url": mail_url,
        "url": url,
    }))

    if as_string:
        return html

    return HttpJsonResponse(
        content=html,
        current_view="content",
        mimetype="text/plain",
    )


def fb_upload_image(request):
    """Uploads an image within filebrowser.

    **Query String:**

        obj-id
            The current object for which the images will be uploaded.

    **Permission:**

        edit
    """
    obj_id = request.POST.get("obj-id")
    obj = lfc.utils.get_content_object(pk=obj_id)
    obj.check_permission(request.user, "edit")

    if request.method == "POST":
        for file_content in request.FILES.values():
            image = Image(content=obj, title=file_content.name)
            image.image.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = (i + 1) * 10
        image.save()

    html = (
        ("#overlay .content", imagebrowser(request, obj_id, as_string=True)),
    )

    return HttpJsonResponse(
        content=html,
        mimetype="text/plain",
        current_view="dummy",   # prevents that the tinymce is updated
    )


def fb_upload_file(request):
    """Uploads file within filebrowser.

    **Query String:**

        obj-id
            The current object for which the images will be uploaded.

    **Permission:**

        edit
    """
    obj_id = request.POST.get("obj-id")
    obj = lfc.utils.get_content_object(pk=obj_id)
    obj.check_permission(request.user, "edit")

    for file_content in request.FILES.values():
        file = File(content=obj, title=file_content.name)
        file.file.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = (i + 1) * 10
        file.save()

    html = (
        ("#overlay .content", filebrowser(request, obj_id, as_string=True)),
    )

    return HttpJsonResponse(
        content=html,
        current_view="content",
        mimetype="text/plain",
    )


# Translations ###############################################################
##############################################################################
def translate_object(request, language, id=None, form_translation=None,
    form_canonical=None, template_name="lfc/manage/object_translate.html"):
    """Dislays the translation form for the object with passed id and language.

    **Parameters:**

        language
            The language to which the object should be translated.

        id
            The id of the object which should be translated.

        form_translation
            If passed this form will taken. Otherwise a new form will be
            created.

        form_canonical
            If passed this form will taken. Otherwise a new form will be
            created.

    **Permission:**

        edit
    """
    obj = get_object_or_404(BaseContent, pk=id)
    obj.check_permission(request.user, "edit")

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
        form_canonical = canonical.get_content_object().edit_form(instance=canonical.get_content_object(), prefix="canonical")

    if translation:
        translation = translation.get_content_object()

    if form_translation is None:
        form_translation = canonical.get_content_object().edit_form(instance=translation, prefix="translation")

    return render_to_response(template_name, RequestContext(request, {
        "canonical": canonical,
        "form_canonical": form_canonical,
        "form_translation": form_translation,
        "id": id,
        "translation_language": language,
        "translation_id": translation_id,
    }))


def save_translation(request):
    """Saves (adds or edits) a translation.

    **Query String:**

        canonical_id
            The id of the canonical object

        cancel
            If given the translation is considered as canceled.

    **Permission:**

        edit
    """
    canonical_id = request.POST.get("canonical_id")
    canonical = lfc.utils.get_content_object(pk=canonical_id)
    canonical.check_permission(request.user, "edit")

    if request.POST.get("cancel"):
        url = reverse("lfc_manage_object", kwargs={"id": canonical_id})
        msg = _(u"Translation has been canceled.")
        return MessageHttpResponseRedirect(url, msg)

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

    form_canonical = canonical.edit_form(
        prefix="canonical",
        instance=canonical,
        data=request.POST,
        files=request.FILES,
    )

    form_translation = canonical.edit_form(
        prefix="translation",
        instance=translation,
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

        url = reverse("lfc_manage_object", kwargs={"id": translation.id})
        return MessageHttpResponseRedirect(url, msg)
    else:
        return translate_object(request, translation_language, canonical.id, form_translation, form_canonical)


# Template ###################################################################
##############################################################################
def set_template(request):
    """Sets the template of the current object.

    **Query String:**

        obj_id
            The id of the object for which the template should be set.

        template_id
            The id of the template which should be set.

    **Permission:**

        edit
    """
    obj_id = request.POST.get("obj_id")
    obj = lfc.utils.get_content_object(pk=obj_id)
    obj.check_permission(request.user, "edit")

    template_id = request.POST.get("template_id")
    obj.template_id = template_id
    obj.save()

    return HttpResponseRedirect(obj.get_absolute_url())


# Review objects #############################################################
##############################################################################
def review_objects(request, template_name="lfc/manage/review_objects.html"):
    """Displays a list objects which are to reviewed (submitted).

    **Permission:**

        review (on portal)
    """
    portal = get_portal()
    portal.check_permission(request.user, "review")

    review_states = [wst.state for wst in WorkflowStatesInformation.objects.filter(review=True)]

    objs = []
    for obj in lfc.utils.get_content_objects():
        if obj.get_state() in review_states:
            objs.append(obj)

    return render_to_response(template_name, RequestContext(request, {
        "objs": objs,
    }))


# Workflow ###################################################################
##############################################################################
def do_transition(request, id):
    """Processes passed transition for object with passed id.

    **Parameters:**

        id
            The id of the object for which the transition should be done.

    **Query String:**

        transition
            The id of the transition which should be performed.
    """
    transition = request.REQUEST.get("transition")
    try:
        transition = Transition.objects.get(pk=transition)
    except Transition.DoesNotExist:
        pass
    else:
        obj = lfc.utils.get_content_object(pk=id)

        if transition.permission:
            obj.check_permission(request.user, transition.permission.codename)

        workflows.utils.do_transition(obj, transition, request.user)

        # CACHE
        cache_key_1 = "%s-obj-%s" % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, obj.get_absolute_url()[1:])
        lfc.utils.delete_cache([cache_key_1])

        # Set publication date
        if obj.publication_date is None:
            public_states = [wst.state for wst in WorkflowStatesInformation.objects.filter(public=True)]
            if obj.get_state() in public_states:
                obj.publication_date = datetime.datetime.now()
                obj.save()

    html = (
        ("#menu", object_menu(request, obj)),
        ("#navigation", navigation(request, obj)),
        ("#tabs-inline", object_tabs(request, obj)),
    )

    return HttpJsonResponse(
        content=html,
        message=_(u"The state has been changed."),
        tabs=True,
        mimetype="text/plain",
    )


def manage_workflow(request, id=None, template_name="lfc/manage/workflow.html"):
    """Displays the main management form for the workflow with given id. If
       the id is not given an add form is displayed.

    **Parameters:**

        id
            The id of the workflow which should be managed.

    **Permission:**

        manage_portal

    """
    get_portal().check_permission(request.user, "manage_portal")
    workflows = Workflow.objects.all()

    if id:
        workflow = Workflow.objects.get(pk=id)
    else:
        try:
            workflow = workflows[0]
        except IndexError:
            return HttpResponseRedirect(reverse("lfc_manage_add_workflow"))
        else:
            return HttpResponseRedirect(
                reverse("lfc_manage_workflow", kwargs={"id": workflow.id}))

    return render_to_response(template_name, RequestContext(request, {
        "data": workflow_data(request, workflow),
        "states": workflow_states(request, workflow),
        "transitions": workflow_transitions(request, workflow),
        "menu": workflow_menu(request, workflow),
        "navigation": workflow_navigation(request, workflow),
        "workflow": workflow,
    }))


def workflow_data(request, workflow, template_name="lfc/manage/workflow_data.html"):
    """Displays the data tab of the workflow with passed workflow.

    **Parameters:**

        workflow
            The workflow for which the data should be displayed.

    **Permission:**

        None
    """
    form = WorkflowForm(instance=workflow)

    selected = [w.permission for w in WorkflowPermissionRelation.objects.filter(workflow=workflow)]

    permissions = []
    for permission in Permission.objects.all():
        permissions.append({
            "id": permission.id,
            "name": permission.name,
            "checked": permission in selected,
        })

    return render_to_string(template_name, RequestContext(request, {
        "workflow": workflow,
        "form": form,
        "permissions": permissions,
    }))


def workflow_states(request, workflow, template_name="lfc/manage/workflow_states.html"):
    """Displays the states tab of the passed workflow.

    **Parameters:**

        workflow
            The workflow for which the states should be displayed.

    **Permission:**

        None
    """
    return render_to_string(template_name, RequestContext(request, {
        "workflow": workflow,
    }))


def workflow_transitions(request, workflow, template_name="lfc/manage/workflow_transitions.html"):
    """Displays the transitions tab of the passed workflow.

    **Parameters:**

        workflow
            The workflow for which the transitions should be displayed.

    **Permission:**

        None
    """
    return render_to_string(template_name, RequestContext(request, {
        "workflow": workflow,
    }))


def workflow_menu(request, workflow=None, template_name="lfc/manage/workflow_menu.html"):
    """Displays the horizontal menu of the workflow

    **Parameters:**

        workflow
            The workflow for which the menu should be displayed.

    **Permission:**

        None
    """
    return render_to_string(template_name, RequestContext(request, {
        "workflow": workflow,
    }))


def workflow_navigation(request, workflow=None, template_name="lfc/manage/workflow_navigation.html"):
    """Displays the left side navigation of a workflow

    **Parameters:**

        workflow
            The current displayed workflow.

    **Permission:**

        None
    """
    return render_to_string(template_name, RequestContext(request, {
        "current_workflow": workflow,
        "workflows": Workflow.objects.all()
    }))


# actions
def save_workflow_data(request, id):
    """Saves the workflow data.

    **Parameters:**

        id
            The id of the workflow for which the data should be saved.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")
    workflow = Workflow.objects.get(pk=id)

    form = WorkflowForm(instance=workflow, data=request.POST)
    if form.is_valid:
        form.save()

    selected = request.POST.getlist("permission")

    for permission in Permission.objects.all():
        if str(permission.id) in selected:
            WorkflowPermissionRelation.objects.get_or_create(workflow=workflow, permission=permission)
        else:
            try:
                wpr = WorkflowPermissionRelation.objects.get(workflow=workflow, permission=permission)
            except WorkflowPermissionRelation.DoesNotExist:
                pass
            else:
                wpr.delete()

    html = (
        ("#data", workflow_data(request, workflow)),
        ("#navigation", workflow_navigation(request, workflow)),
    )

    return return_as_json(html, _(u"Workflow data has been saved."))


def add_workflow(request, template_name="lfc/manage/workflow_add.html"):
    """Displays an add form to add an workflow (GET). Creates a new workflow
    if the form is valid (POST).

    **Permission:**

        manage_portal

    """
    get_portal().check_permission(request.user, "manage_portal")

    if request.method == "POST":
        form = WorkflowAddForm(data=request.POST)
        if form.is_valid():
            workflow = form.save()
            return MessageHttpResponseRedirect(
                reverse("lfc_manage_workflow", kwargs={"id": workflow.id}),
                _(u"Workflow has been added."))
    else:
        form = WorkflowAddForm()

    return render_to_response(template_name, RequestContext(request, {
        "form": form,
        "menu": workflow_menu(request),
        "navigation": workflow_navigation(request),
    }))


def delete_workflow(request, id):
    """Deletes the workflow with the passed id.

    **Parameters:**

        id
            The id of the workflow which should be deleted.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    try:
        workflow = Workflow.objects.get(pk=id)
    except Workflow.DoesNotExist:
        pass
    else:
        for ctr in ContentTypeRegistration.objects.filter(workflow=workflow):
            ctr.workflow = None
            ctr.save()
        workflow.delete()

    return MessageHttpResponseRedirect(
        reverse("lfc_manage_workflow"), _(u"Workflow has been deleted."))

def update_all_permissions(request):
    """Updates the permissions of all objects to their current workflow state
    """
    get_portal().check_permission(request.user, "manage_portal")
    for obj in lfc.utils.get_content_objects():
        workflows.utils.update_permissions(obj)
    return MessageHttpResponseRedirect(reverse("lfc_manage_utils"), _(u"Permissions have been updated."))


# Workflow state #############################################################
##############################################################################
def manage_state(request, id, template_name="lfc/manage/workflow_state.html"):
    """Displays a form to manage the workflow state with the given id.

    **Parameters:**

        id
            The id of the workflow state which should be displayed.

    **Permission:**

        manage_portal

    """
    get_portal().check_permission(request.user, "manage_portal")
    state = State.objects.get(pk=id)
    workflow = state.workflow

    form = StateForm(instance=state)

    roles = Role.objects.all()

    permissions = []
    for permission in workflow.permissions.all():
        roles_temp = []
        for role in roles:
            try:
                StatePermissionRelation.objects.get(state=state, permission=permission, role=role)
            except StatePermissionRelation.DoesNotExist:
                checked = False
            else:
                checked = True

            roles_temp.append({
                "id": role.id,
                "name": role.name,
                "checked": checked,
            })

        try:
            StateInheritanceBlock.objects.get(state=state, permission=permission)
        except StateInheritanceBlock.DoesNotExist:
            inherited = True
        else:
            inherited = False

        permissions.append({
            "id": permission.id,
            "name": permission.name,
            "roles": roles_temp,
            "inherited": inherited,
        })

    try:
        wsi = WorkflowStatesInformation.objects.get(state=state)
    except WorkflowStatesInformation.DoesNotExist:
        public = False
        review = False
    else:
        public = wsi.public
        review = wsi.review

    content = render_to_string(template_name, RequestContext(request, {
        "state": state,
        "form": form,
        "permissions": permissions,
        "roles": roles,
        "public": public,
        "review": review,
    }))

    return HttpJsonResponse(
        content=[["#overlay .content", content]],
        open_overlay=True,
        mimetype="text/plain",
    )


def save_workflow_state(request, id):
    """Saves the workflow state with passed id.

    **Parameters:**

        id
            The id of the workflow state which should be saved.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    state = State.objects.get(pk=id)

    form = StateForm(instance=state, data=request.POST)
    if form.is_valid:
        form.save()

    # Workflow information
    wsi, created = WorkflowStatesInformation.objects.get_or_create(state=state)
    if request.POST.get("public"):
        wsi.public = True
    else:
        wsi.public = False

    if request.POST.get("review"):
        wsi.review = True
    else:
        wsi.review = False

    wsi.save()

    role_permssion_ids = request.POST.getlist("role_permission_id")
    inherited_ids = request.POST.getlist("inherited_id")

    workflow_permissions = [wpr.permission for wpr in WorkflowPermissionRelation.objects.filter(workflow = state.workflow)]
    StateInheritanceBlock.objects.filter(state=state).delete()
    StatePermissionRelation.objects.filter(state=state).delete()

    for role in Role.objects.all():
        for permission in workflow_permissions:
            # Inheritance
            if str(permission.id) not in inherited_ids:
                StateInheritanceBlock.objects.get_or_create(state=state, permission=permission)

            # Roles
            role_permission_id = "%s|%s" % (role.id, permission.id)
            if role_permission_id in role_permssion_ids:
                StatePermissionRelation.objects.get_or_create(state=state, role=role, permission=permission)

    content = (
        ("#data", workflow_data(request, state.workflow)),
        ("#states", workflow_states(request, state.workflow)),
    )

    return HttpJsonResponse(
        content=content,
        message=_(u"State has been saved."),
        close_overlay=True,
        mimetype="text/plain"
    )


def add_workflow_state(request, id):
    """Adds worfklow state to workflow.

    **Parameters:**

        id
            The id of the workflow to which the state should be added.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    name = request.POST.get("name")
    if name != "":
        state = State.objects.create(workflow_id=id, name=name)

    html = (
        ("#data", workflow_data(request, state.workflow)),
        ("#states", workflow_states(request, state.workflow)),
    )

    return return_as_json(html, _(u"State has been added."))


def delete_workflow_state(request, id):
    """Deletes the transition with passed id.

    **Parameters:**

        id
            The id of the state which should be deleted.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    try:
        state = State.objects.get(pk=id)
    except State.DoesNotExist:
        pass
    else:
        workflow = state.workflow
        if state.workflow.get_initial_state() == state:
            state.workflow.initial_state = None
            state.workflow.save()
        state.delete()

    html = (
        ("#data", workflow_data(request, workflow)),
        ("#states", workflow_states(request, workflow)),
    )

    return return_as_json(html, _(u"State has been deleted."))


# Workflow transition ########################################################
##############################################################################
def manage_transition(request, id, template_name="lfc/manage/workflow_transition.html"):
    """Displays the management form of a transition.

    **Parameters:**

        id
            The id of the transition which should be displayed.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    transition = Transition.objects.get(pk=id)
    form = TransitionForm(instance=transition)

    content = render_to_string(template_name, RequestContext(request, {
        "transition": transition,
        "form": form,
    }))

    return HttpJsonResponse(
        content=[["#overlay .content", content]],
        open_overlay=True,
        mimetype="text/plain",
    )


def save_workflow_transition(request, id):
    """Saves the workflow state with passed id.

    **Parameters:**

        id
            The id of the transition which should be saved.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")
    transition = Transition.objects.get(pk=id)

    form = TransitionForm(instance=transition, data=request.POST)
    if form.is_valid:
        form.save()

    content = (
        ("#transitions", workflow_transitions(request, transition.workflow)),
        ("#states", workflow_states(request, transition.workflow)),
    )

    return HttpJsonResponse(
        content=content,
        message=_(u"Transition has been saved."),
        close_overlay=True,
        mimetype="text/plain",
    )


def add_workflow_transition(request, id):
    """Adds a transition to the workflow with passed id. The name of the
    transition must be with the name parameter within the post request.

    **Parameters:**

        id
            The id of the workflow to which the transition should be added.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")
    workflow = Workflow.objects.get(pk=id)

    name = request.POST.get("name")
    if name != "":
        Transition.objects.create(workflow=workflow, name=name)

    html = (
        ("#transitions", workflow_transitions(request, workflow)),
    )

    return return_as_json(html, _(u"Transition has been added."))


def delete_workflow_transition(request, id):
    """Deletes the transition with passed id.

    **Parameters:**

        id
            The id of the transition which should be deleted.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    try:
        transition = Transition.objects.get(pk=id)
        workflow = transition.workflow
    except Transition.DoesNotExist:
        pass
    else:
        transition.delete()

    html = (
        ("#transitions", workflow_transitions(request, workflow)),
    )

    return return_as_json(html, _(u"Transition has been deleted."))


# Cut/Copy and paste #########################################################
##############################################################################
def lfc_copy(request, id):
    """Puts the object with passed id to the clipboard and marks it as copied.

    **Parameters:**

        id
            The id of the object which should be copied to the clipboard

    **Permission:**

        add
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "add")

    request.session["clipboard"] = [id]
    request.session["clipboard_action"] = COPY

    obj = lfc.utils.get_content_object(pk=id)

    html = (
        ("#menu", object_menu(request, obj)),
    )

    return return_as_json(html, _(u"The object has been put to the clipboard."))


def cut(request, id):
    """Puts the object within passed id into the clipboard and marks it as
    cut.

    **Parameters:**

        id
            The id of the object which should be put to the clipboard.

    **Permission:**

        delete
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj.check_permission(request.user, "delete")

    request.session["clipboard"] = [id]
    request.session["clipboard_action"] = CUT

    obj = lfc.utils.get_content_object(pk=id)

    html = (
        ("#menu", object_menu(request, obj)),
    )

    return return_as_json(html, _(u"The object has been put to the clipboard."))


def paste(request, id=None):
    """Pastes the object stored in the clipboard to object with given id. If
    the object is None it pasted the object to the portal.

    **Parameters:**

        id
            The id of the object which should to which the clipboard should be
            pasted.

    **Permission:**

        add
    """
    if id:
        obj = lfc.utils.get_content_object(pk=id)
        obj.check_permission(request.user, "add")
        menu = object_menu(request, obj)
        children = object_children(request, obj)
    else:
        obj = None
        portal = get_portal()
        portal.check_permission(request.user, "add")
        menu = portal_menu(request, portal)
        children = portal_children(request, portal)

    message = _paste(request, obj)

    html = (
        ("#menu", menu),
        ("#navigation", navigation(request, obj)),
        ("#children", children),
    )

    return return_as_json(html, message)


# Content types ##############################################################
##############################################################################
def content_types(request):
    """Redirects to the first content type.
    """
    get_portal().check_permission(request.user, "manage_portal")

    ctr = ContentTypeRegistration.objects.filter()[0]
    url = reverse("lfc_content_type", kwargs={"id": ctr.id})
    return HttpResponseRedirect(url)


def content_type(request, id, template_name="lfc/manage/content_types.html"):
    """Displays the main screen of the content type management (GET) and
    saves the displayed content type (POST).

    **Parameters:**

        id
            The id of the content type which should be displayed.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    ctr = ContentTypeRegistration.objects.get(pk=id)
    ctype = ContentType.objects.get(model=ctr.type)

    old_workflow = ctr.workflow

    if old_workflow:
        old_objects = old_workflow.get_objects()
    else:
        old_objects = []

    message = ""
    if request.method == "POST":
        form = ContentTypeRegistrationForm(data=request.POST, instance=ctr)
        if form.is_valid():
            message = _(u"Content type has been saved.")
            form.save()
            if ctr.workflow:
                # if there is an old worfklow set workflow state to all
                # content type instances which had the old workflow
                if old_workflow and ctr.workflow != old_workflow:
                    workflows.utils.set_workflow_for_model(ctype, ctr.workflow)
                    for obj in old_objects:
                        if obj.content_type == ctr.type:
                            obj.set_state(ctr.workflow.get_initial_state())
                # If there is no old workflow set the initial workflow state
                # to all content type instances which get the new workflow
                elif old_workflow is None:
                    workflows.utils.set_workflow_for_model(ctype, ctr.workflow)
                    for obj in ctr.workflow.get_objects():
                        if obj.content_type == ctr.type:
                            obj.set_state(ctr.workflow.get_initial_state())

            else:
                workflows.utils.remove_workflow_from_model(ctype)
    else:
        ctr.workflow = workflows.utils.get_workflow_for_model(ctype)
        ctr.save()
        form = ContentTypeRegistrationForm(instance=ctr)

    response = render_to_response(template_name, RequestContext(request, {
        "types": ContentTypeRegistration.objects.all(),
        "ctr": ctr,
        "form": form,
    }))

    return lfc.utils.set_message_to_reponse(response, message)


# Applications ###############################################################
##############################################################################
def applications(request, template_name="lfc/manage/applications.html"):
    """Displays install/uninstall applications view.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

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
                "name": app_name,
                "installed": installed,
                "pretty_name": getattr(module, "name", app_name),
                "description": getattr(module, "description", None),
            })

    return render_to_response(template_name, RequestContext(request, {
        "applications": applications,
    }))


def install_application(request, name):
    """Installs LFC application with passed name.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    import_module(name).install()
    try:
        Application.objects.create(name=name)
    except Application.DoesNotExist:
        pass

    url = reverse("lfc_applications")
    return HttpResponseRedirect(url)


def reinstall_application(request, name):
    """Reinstalls LFC application with passed name.

    **Parameters:**

        name
            The name of the application.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

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

    **Parameters:**

        name
            The name of the application.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    import_module(name).uninstall()
    try:
        application = Application.objects.get(name=name)
    except Application.DoesNotExist:
        pass
    else:
        application.delete()

    url = reverse("lfc_applications")
    return HttpResponseRedirect(url)


# Users ######################################################################
##############################################################################
def manage_users(request, template_name="lfc/manage/users.html"):
    """Displays an overview over all users.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    return render_to_response(template_name, RequestContext(request, {
        "users": users_inline(request),
    }))


def users_inline(request, template_name="lfc/manage/users_inline.html"):
    """Displays details of the manager user view. Factored out to be used
    for initial call and subsequent ajax calls.

    **Permission:**

        None (as this is not called from outside)
    """
    users = _get_filtered_users(request, "users")
    paginator = Paginator(users, 20)
    p = request.session.get("page", request.REQUEST.get("page", 1))

    try:
        page = paginator.page(p)
    except EmptyPage:
        page = 0

    return render_to_string(template_name, RequestContext(request, {
        "users": users,
        "paginator": paginator,
        "page": page,
        "name_filter": request.session.get("users_name_filter", ""),
        "active_filter": request.session.get("users_active_filter", "")
    }))


def change_users(request):
    """Updates or deletes checked users.

    **Query String:**

        action
            The action which should be performed. One of: delete, update.

        active_ids
            A list of ids of users which should be active.

        user_ids
            A list of user ids which are considered to be updated.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    if request.POST.get("action") == "delete":
        ids = request.POST.getlist("delete_ids")
        users = User.objects.filter(pk__in=ids)
        users.delete()
        message = _(u"Users have been deleted.")
    else:
        message = _(u"Users have been updated.")
        active_ids = request.POST.getlist("active_ids")
        for id in request.POST.getlist("user_ids"):
            user = User.objects.get(pk=id)
            if id in active_ids:
                user.is_active = True
            else:
                user.is_active = False
            user.save()

    html = (("#users", users_inline(request)), )

    result = json.dumps(
        {"html": html, "message": message}, cls=LazyEncoder)

    return HttpResponse(result)


def set_users_page(request):
    """Sets the current user page.

    **Query String:**

        page
            The page of users which should be displayed (pagination).

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")
    request.session["users_page"] = request.GET.get("page", 1)

    user = request.GET.get("user")
    if user:
        html = (("#navigation", user_navigation(request, user)), )
    else:
        html = (("#users", users_inline(request)), )

    result = json.dumps({"html": html}, cls=LazyEncoder)
    return HttpResponse(result)


def set_users_filter(request):
    """Sets the user filter for the user overview display.

    **Query String:**

        users_active_filter
            The filter which should be used for the active field.

        users_name_filter
            The filter which should be used for the name field.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    _update_filter(request, "users_active_filter")
    _update_filter(request, "users_name_filter")
    request.session["users_page"] = 1

    message = _(u"Filter has been set.")
    html = (("#users", users_inline(request)), )

    result = json.dumps(
        {"html": html, "message": message}, cls=LazyEncoder)

    return HttpResponse(result)


def reset_users_filter(request):
    """Resets the user filter for the user overview display.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    _delete_filter(request, "users_name_filter")
    _delete_filter(request, "users_active_filter")
    _delete_filter(request, "users_page")

    message = _(u"Filter has been reset.")

    user = request.GET.get("user")
    if user:
        html = (("#navigation", user_navigation(request, user)), )
    else:
        html = (("#users", users_inline(request)), )

    result = json.dumps(
        {"html": html, "message": message}, cls=LazyEncoder)

    return HttpResponse(result)


# User #######################################################################
##############################################################################
def manage_user(request, id=None, template_name="lfc/manage/user.html"):
    """Displays the manage user form.

    **Parameters:**

        id
            The id of the user which should be displayed

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    if id is None:
        user = User.objects.all()[0]
        return HttpResponseRedirect(reverse("lfc_manage_user", kwargs={"id": user.id}))

    result = render_to_response(template_name, RequestContext(request, {
        "data": user_data(request, id),
        "password": user_password(request, id),
        "menu": user_menu(request, id),
        "navigation": user_navigation(request, id),
        "current_user_id": id,
        "user_name_filter": request.session.get("user_name_filter", "")
    }))

    return HttpResponse(result)


def user_menu(request, id, template_name="lfc/manage/user_menu.html"):
    """Displays the menu within user management.

    **Parameters:**

        id
            The id of the user which should be displayed

    **Permission:**

        None (as this is not called from outside)
    """
    return render_to_string(template_name, RequestContext(request, {
        "current_user_id": id,
        "display_delete": id != "1",
    }))


def user_data(request, id, template_name="lfc/manage/user_data.html"):
    """Displays the user data form of the user with passed id.

    **Parameters:**

        id
            The id of the user which should be displayed

    **Permission:**

        None (as this is not called from outside)
    """
    user = User.objects.get(pk=id)

    if request.method == "POST":
        form = UserForm(instance=user, data=request.POST)
    else:
        form = UserForm(instance=user)

    return render_to_string(template_name, RequestContext(request, {
        "myuser": user,
        "form": form,
    }))


def user_password(request, id, form=None, template_name="lfc/manage/user_password.html"):
    """Displays the change password form for the user with passed id.

    **Parameters:**

        id
            The id of the user which should be displayed

    **Permission:**

        None (as this is not called from outside)
    """
    user = User.objects.get(pk=id)

    if request.method == "POST":
        form = AdminPasswordChangeForm(user, request.POST)
    else:
        form = AdminPasswordChangeForm(user)

    return render_to_string(template_name, RequestContext(request, {
        "form": form,
        "user_id": user.id,
    }))


def user_navigation(request, id, template_name="lfc/manage/user_navigation.html"):
    """Displays the user navigation.

    **Parameters:**

        id
            The id of the user which should be displayed

    **Permission:**

        None (as this is not called from outside)
    """
    users = _get_filtered_users(request, "user")
    paginator = Paginator(users, 30)
    page = request.session.get("user_page", request.REQUEST.get("page", 1))

    try:
        page = paginator.page(page)
    except EmptyPage:
        page = 0

    return render_to_string(template_name, RequestContext(request, {
        "current_user_id": int(id),
        "paginator": paginator,
        "page": page,
    }))


# actions
def save_user_data(request, id):
    """Saves the user data form of the user with the passed id.

    **Parameters:**

        id
            The id of the user which should be saved.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    user = User.objects.get(pk=id)
    form = UserForm(instance=user, data=request.POST)

    if form.is_valid():
        form.save()
        message = _(u"User has been saved")
    else:
        message = _(u"An error occured.")

    html = (
        ("#data", user_data(request, id)),
        ("#navigation", user_navigation(request, id)),
        ("#user_fullname", "%s %s" % (user.first_name, user.last_name)),
        ("#username", user.username),
    )

    result = json.dumps(
        {"html": html, "message": message}, cls=LazyEncoder)

    return HttpResponse(result)


def change_password(request, id):
    """Changes the password for the user with given id. This is just for portal
    managers which means users which have the manage_portal permission.

    **Parameters:**

        id
            The id of the user which password should be changed.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    user = User.objects.get(pk=id)
    form = AdminPasswordChangeForm(user, request.POST)

    if form.is_valid():
        form.save()
        message = _(u"Password has been changed.")
    else:
        message = _(u"An error occured.")

    html = (("#password", user_password(request, id, form)), )

    result = json.dumps(
        {"html": html, "message": message}, cls=LazyEncoder)

    return HttpResponse(result)


def add_user(request, template_name="lfc/manage/user_add.html"):
    """Displays a form to add an user (GET) and adds it (POST).

    **Query String:**

        password1
            The password of the user.

        roles
            A list of role ids which should be assigned to the user.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    if request.method == "POST":
        form = UserAddForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(request.POST.get("password1"))

            role_ids = request.POST.getlist("roles")
            for role in Role.objects.all():

                if str(role.id) in role_ids:
                    try:
                        prr = PrincipalRoleRelation.objects.get(user=user, role=role)
                    except PrincipalRoleRelation.DoesNotExist:
                        PrincipalRoleRelation.objects.create(user=user, role=role)
                else:
                    try:
                        prr = PrincipalRoleRelation.objects.get(user=user, role=role)
                    except PrincipalRoleRelation.DoesNotExist:
                        pass
                    else:
                        prr.delete()

            user.save()

            url = reverse("lfc_manage_user", kwargs={"id": user.id})
            message = _(u"User has been added.")
            return MessageHttpResponseRedirect(url, message)

        else:
            return render_to_response(template_name, RequestContext(request, {
                "form": form,
                "navigation": user_navigation(request, 0),
            }))
    else:
        form = UserAddForm()
        return render_to_response(template_name, RequestContext(request, {
            "form": form,
            "navigation": user_navigation(request, 0),
        }))


def delete_user(request, id):
    """Deletes the user with the passed id

    **Parameters:**

        id
            The id of the user which should be deleted.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    try:
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        pass
        message = _(u"User couldn't deleted.")
    else:
        user.delete()
        message = _(u"User has been deleted.")

    user = User.objects.all()[0]
    url = reverse("lfc_manage_user", kwargs={"id": user.id})
    return MessageHttpResponseRedirect(url, message)


def set_user_page(request):
    """Sets the current user page of paginated users.

    **Query String:**

        page
            The page which should be displayed.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    request.session["user_page"] = request.GET.get("page", 1)
    user = request.GET.get("user")

    html = (("#navigation", user_navigation(request, user)), )
    result = json.dumps({"html": html}, cls=LazyEncoder)
    return HttpResponse(result)


def set_user_filter(request):
    """Sets the filter for the user management display.

    **Query String:**

        user_name_filter
            The filter for the user name

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    user = request.GET.get("user")

    _update_filter(request, "user_name_filter")
    request.session["user_page"] = 1

    html = (("#navigation", user_navigation(request, user)), )
    result = json.dumps({"html": html}, cls=LazyEncoder)
    return HttpResponse(result)


def reset_user_filter(request):
    """Resets the filter for the user management display.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    _delete_filter(request, "user_name_filter")
    _delete_filter(request, "user_page")

    message = _(u"Filter has been reset.")

    user = request.GET.get("user")
    html = (("#navigation", user_navigation(request, user)), )
    result = json.dumps({"html": html, "message": message}, cls=LazyEncoder)
    return HttpResponse(result)


# Group ######################################################################
# ############################################################################
def manage_group(request, id=None, template_name="lfc/manage/group.html"):
    """Displays the manage group form. Or the add group form if no group exists
    yet.

    **Parameters:**

        id
            The id of the group which should be displayed.
    """
    get_portal().check_permission(request.user, "manage_portal")

    if id is None:
        try:
            id = Group.objects.all()[0].id
            return HttpResponseRedirect(reverse("lfc_manage_group", kwargs={"id": id}))
        except IndexError:
            return render_to_response("lfc/manage/group_none.html", RequestContext(request, {}))

    group = Group.objects.get(pk=id)

    form = GroupForm(instance=group)
    return render_to_response(template_name, RequestContext(request, {
        "form": form,
        "group": group,
        "groups": Group.objects.all(),
        "current_group_id": group.id,
        "users" : group.user_set.all(),
    }))


def add_group(request, template_name="lfc/manage/group_add.html"):
    """Displays the add group form (GET) and adds a new group (POST).

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    if request.method == "POST":
        form = GroupForm(data=request.POST)
        if form.is_valid():
            group = form.save()
            return HttpResponseRedirect(reverse("lfc_manage_group", kwargs={"id": group.id}))
        else:
            return render_to_response(template_name, RequestContext(request, {
                "form": form,
                "groups": Group.objects.all(),
            }))
    else:
        form = GroupForm()
        return render_to_response(template_name, RequestContext(request, {
            "form": form,
            "groups": Group.objects.all(),
        }))


def delete_group(request, id):
    """Deletes the group with the passed id.

    **Parameters:**

        id
            The id of the group which should be deleted.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    try:
        Group.objects.get(pk=id).delete()
    except Group.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse("lfc_manage_group"))


def save_group(request, id, template_name="lfc/manage/group_add.html"):
    """Saves group with passed id.

    **Parameters:**

        id
            The id of the group which should be deleted.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    group = Group.objects.get(pk=id)
    form = GroupForm(instance=group, data=request.POST)
    if form.is_valid():
        group = form.save()
        return HttpResponseRedirect(reverse("lfc_manage_group", kwargs={"id": group.id}))
    else:
        return render_to_response(template_name, RequestContext(request, {
            "form": form,
            "group": group,
            "groups": Group.objects.all(),
            "current_group_id": int(id),
        }))


# Roles ######################################################################
# ############################################################################
def manage_role(request, id=None, template_name="lfc/manage/role.html"):
    """Displays the manage role form. Or the add role form if there is no role
    yet.

    **Parameters:**

        id
            The id of the role which should be displayed. If this is None the
            role add form will be displayed.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    if id is None:
        try:
            role = Role.objects.exclude(name__in=("Anonymous", "Owner"))[0]
        except IndexError:
            return HttpResponseRedirect(reverse("lfc_manage_add_role"))
        else:
            return HttpResponseRedirect(reverse("lfc_manage_role", kwargs={"id": role.id}))

    role = Role.objects.get(pk=id)
    if role.name in ["Anonymous", "Owner"]:
        raise Http404

    form = RoleForm(instance=role)

    return render_to_response(template_name, RequestContext(request, {
        "form": form,
        "role": role,
        "roles": Role.objects.exclude(name__in=("Anonymous", "Owner")),
        "users" : role.get_users(),
        "current_role_id": int(id),
    }))


def add_role(request, template_name="lfc/manage/role_add.html"):
    """Displays the add role form (GET) and adds a new role (POST).

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    if request.method == "POST":
        form = RoleForm(data=request.POST)
        if form.is_valid():
            role = form.save()
            return HttpResponseRedirect(reverse("lfc_manage_role", kwargs={"id": role.id}))
        else:
            return render_to_response(template_name, RequestContext(request, {
                "form": form,
            }))
    else:
        form = RoleForm()
        return render_to_response(template_name, RequestContext(request, {
            "form": form,
            "roles": Role.objects.exclude(name__in=("Anonymous", "Owner")),
        }))


def delete_role(request, id, template_name="lfc/manage/role_add.html"):
    """Deletes the role with the passed id.

    **Parameters:**

        id
            The id of the group which should be deleted.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    try:
        Role.objects.get(pk=id).delete()
    except Role.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse("lfc_manage_role"))


def save_role(request, id, template_name="lfc/manage/role_add.html"):
    """Saves role with passed id.

    **Parameters:**

        id
            The id of the role which should be saved.

    **Permission:**

        manage_portal
    """
    get_portal().check_permission(request.user, "manage_portal")

    role = Role.objects.get(pk=id)
    form = RoleForm(instance=role, data=request.POST)
    if form.is_valid():
        role = form.save()
        return HttpResponseRedirect(reverse("lfc_manage_role", kwargs={"id": role.id}))
    else:
        return render_to_response(template_name, RequestContext(request, {
            "form": form,
            "role": role,
            "roles": Role.objects.exclude(name__in=("Anonymous", "Owner")),
            "current_role_id": int(id),
        }))

# Utils
def manage_utils(request, template_name="lfc/manage/utils.html"):
    """Displays the overview over all utils.
    """
    return render_to_response(template_name, RequestContext(request, {
    }))

def reindex_objects(request):
    """Reindexes the searchable text of all content objects.
    """
    for obj in lfc.utils.get_content_objects():
        obj.reindex()

    return MessageHttpResponseRedirect(reverse("lfc_manage_utils"), _(u"Objects have been reindexed."))

# Private Methods ############################################################
##############################################################################
def _get_filtered_users(request, prefix):
    """Returns filtered users based on the current user filters.
    """
    q = None
    name_filter = request.session.get("%s_name_filter" % prefix)
    if name_filter:
        q = Q(first_name__icontains=name_filter) | \
            Q(last_name__icontains=name_filter) | \
            Q(email__icontains=name_filter) | \
            Q(username__icontains=name_filter)

    active_filter = request.session.get("%s_active_filter" % prefix)
    if active_filter:
        if q:
            q &= Q(is_active=active_filter)
        else:
            q = Q(is_active=active_filter)

    if q:
        users = User.objects.filter(q).order_by("username", )
    else:
        users = User.objects.all().order_by("username", )

    return users


def _delete_filter(request, name):
    """Deletes a filter with passed name.
    """
    if name in request.session.keys():
        del request.session[name]


def _update_filter(request, name):
    """Updates filter with passed name.
    """
    filter = request.GET.get(name, "")
    if filter != "":
        request.session[name] = filter
    else:
        if name in request.session.keys():
            del request.session[name]


def _update_children(request, obj):
    """Updates the children of the passed object. Returns a message which can
    be displayed to the user.
    """
    action = request.POST.get("action")
    if action == "delete":
        not_deleted_objs = False
        for key in request.POST.keys():
            if key.startswith("delete-"):
                try:
                    id = key.split("-")[1]
                    child = lfc.utils.get_content_object(pk=id)
                    if not child.has_permission(request.user, "delete"):
                        not_deleted_objs = True
                    else:
                        ctype = ContentType.objects.get_for_model(child)
                        _remove_fks(child)

                        # Deletes files on file system
                        child.images.all().delete()
                        child.files.all().delete()

                        # Delete workflows stuff
                        StateObjectRelation.objects.filter(
                            content_id=child.id, content_type=ctype).delete()

                        # Delete permissions stuff
                        ObjectPermission.objects.filter(
                            content_id=child.id, content_type=ctype).delete()
                        ObjectPermissionInheritanceBlock.objects.filter(
                            content_id=child.id, content_type=ctype).delete()

                        child.delete()
                except (IndexError, BaseContent.DoesNotExist):
                    pass

        if not_deleted_objs:
            message = _(u"Objects have been deleted. (Note: Some objects are not deleted because you haven't the permission to do that).")
        else:
            message = _(u"Objects have been deleted.")
        if isinstance(obj, Portal):
            _update_positions(None)
        else:
            _update_positions(obj)

    elif action == "copy":
        not_copied_objs = False
        ids = []
        for key in request.POST.keys():
            if key.startswith("delete-"):
                id = key.split("-")[1]
                child = lfc.utils.get_content_object(pk=id)
                if not child.has_permission(request.user, "add"):
                    not_copied_objs = True
                else:
                    ids.append(id)
            request.session["clipboard"] = ids
            request.session["clipboard_action"] = COPY
        if not_copied_objs:
            message = _(u"Objects have been put to the clipboard. (Note: Some objects are not put into clipboard because you haven't the permission to do that).")
        else:
            message = _(u"Objects have been put to the clipboard.")

    elif action == "cut":
        not_cutted_objs = False
        ids = []
        for key in request.POST.keys():
            if key.startswith("delete-"):
                id = key.split("-")[1]
                child = lfc.utils.get_content_object(pk=id)
                if not child.has_permission(request.user, "delete"):
                    not_cutted_objs = True
                else:
                    ids.append(id)
            request.session["clipboard"] = ids
            request.session["clipboard_action"] = CUT
        if not_cutted_objs:
            message = _(u"Objects have been put to the clipboard. (Note: Some objects are not put into clipboard because you haven't the permission to do that).")
        else:
            message = _(u"Objects have been put to the clipboard.")

    elif action == "paste":
        if not obj.has_permission(request.user, "add"):
            message = _("You are not allowed to paste to this object.")
        else:
            message = _paste(request, obj)
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
                            child.save()
                        except ValueError:
                            pass

        if isinstance(obj, Portal):
            _update_positions(None)
        else:
            _update_positions(obj)

    return message


def _update_images(request, obj):
    """Updates the images for the passed object.
    """
    action = request.POST.get("action")
    if action == "delete":
        message = _(u"Images has been deleted.")
        for id in request.POST.getlist("delete-images"):
            try:
                image = Image.objects.get(pk=id).delete()
            except (IndexError, Image.DoesNotExist):
                pass

    elif action == "update":
        message = _(u"Images has been updated.")

        for image in obj.images.all():
            image.title = request.POST.get("title-%s" % image.id)
            image.position = request.POST.get("position-%s" % image.id)
            image.caption = request.POST.get("caption-%s" % image.id)
            image.save()

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = (i + 1) * 10
        image.save()

    return message


def _update_files(request, obj):
    """Saves/Deletes the files for the given object. The object can be a
    content object or the portal.
    """
    action = request.POST.get("action")
    if action == "delete":
        message = _(u"Files has been deleted.")
        for id in request.POST.getlist("delete-files"):
            try:
                file = File.objects.get(pk=id).delete()
            except (IndexError, File.DoesNotExist):
                pass
    elif action == "update":
        message = _(u"Files has been updated.")

        for file in obj.files.all():
            file.title = request.POST.get("title-%s" % file.id)
            file.position = request.POST.get("position-%s" % file.id)
            file.save()

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = (i + 1) * 10
        file.save()

    return message


def _display_paste(request, obj):
    """Returns true if the paste button should be displayed.
    """
    return obj.has_permission(request.user, "add") and \
        "clipboard" in request.session.keys()


def _display_action_menu(request, obj):
    """Returns true if the action menu should be displayed.
    """
    if obj.has_permission(request.user, "add"):
        return True
    elif obj.has_permission(request.user, "delete"):
        return True
    else:
        return False


def _remove_fks(obj):
    """Removes the objects from foreign key fields (in order to not delete
    these related objects).

    **Parameters:**

        obj
            The obj for which the foreign keys should be removes.
    """
    try:
        parent = obj.parent
    except ObjectDoesNotExist:
        parent = None
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
            objs = BaseContent.objects.filter(parent=parent, language=language[0])

        for i, p in enumerate(objs):
            p.position = (i + 1) * 10
            p.save()
            if obj and obj.id == p.id:
                obj = p

    return obj


def _has_permission(obj, role, codename):
    """Checks whether the passed group has passed permission for passed object.

    **Parameters:**

    obj
        The object for which the permission should be checked.

    codename
        The permission's codename which should be checked.

    role
        The role for which the permission should be checked.
    """
    ct = ContentType.objects.get_for_model(obj)

    p = ObjectPermission.objects.filter(
        content_type=ct, content_id=obj.id, role=role, permission__codename=codename)

    if p.count() > 0:
        return True
    return False


def _paste(request, obj):
    """Pastes the clipboard to the passed object. if the obj is None the
    clipboard is pasted to the portal.

    **Parameters:**

        obj
            The target object to which the clipboard is pasted.
    """
    # Try to get the action
    action = request.session.get("clipboard_action", "")
    if action == "":
        _reset_clipboard(request)
        msg = _(u"An error has been occured. Please try again.")
        return msg

    if (obj is None) or isinstance(obj, Portal):
        target = None
        target_id = None
    else:
        target = obj
        target_id = obj.id

    # Get the source objs
    source_ids = request.session.get("clipboard", [])

    error_msg = ""
    for source_id in source_ids:
        try:
            source_obj = lfc.utils.get_content_object(pk=source_id)
        except BaseContent.DoesNotExist:
            error_msg = _(u"Some cut/copied objects has been deleted in the meanwhile.")
            continue

        # Save one parent of source_objs (All source_objs have the same parent)
        # for later update of the positions, see below.
        to_updated_obj = source_obj.parent

        # Copy only allowed sub types to target
        allowed_subtypes = get_allowed_subtypes(target)
        ctr_source = get_info(source_obj)

        if ctr_source not in allowed_subtypes:
            error_msg = _(u"Some objects are not allowed here.")
            continue

        descendants = source_obj.get_descendants()
        if action == CUT:

            # Don't cut and paste to own descendants
            if target in descendants or target == source_obj or target == source_obj.parent:
                error_msg = _(u"The objects can't be pasted in own descendants.")
                break

            source_obj.parent_id = target_id
            source_obj.slug = _generate_slug(source_obj, target)

            if source_obj.language == "0":
                amount = BaseContent.objects.filter(parent=target_id, language__in=("0", translation.get_language())).count()
            else:
                amount = BaseContent.objects.filter(parent=target_id, language__in=("0", source_obj.language)).count()

            source_obj.position = (amount + 1) * 10
            source_obj.save()

            _reset_clipboard(request)
        else:
            # Paste
            target_obj = copy.deepcopy(source_obj)
            target_obj.pk = None
            target_obj.id = None
            target_obj.parent_id = target_id

            amount = BaseContent.objects.filter(parent=target_id, language__in=("0", source_obj.language)).count()
            target_obj.position = (amount + 1) * 10

            target_obj.slug = _generate_slug(source_obj, target)

            # Workaround for django-tagging
            try:
                target_obj.save()
            except IntegrityError:
                pass

            # Prevent recursion
            if target not in descendants and target != source_obj:
                _copy_descendants(source_obj, target_obj)

    if error_msg:
        msg = error_msg
    else:
        _update_positions(to_updated_obj)
        msg = _(u"The object has been pasted.")

    return msg


def _generate_slug(source_obj, parent):
    """Generates a unique slug for passed source_obj in passed parent

    **Parameters:**

        source_obj
            The object for which the slug should be generated

        parent
            The object in which the source_obj should be pasted. The slug
            which is created is unique within parent.
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
    if "clipboard" in request.session.keys():
        del request.session["clipboard"]
    if "clipboard_action" in request.session.keys():
        del request.session["clipboard_action"]


def _copy_descendants(source_obj, target_obj):
    """Copies all descendants (recursively) from source_obj to target_obj.
    This includes: children, images, files, portlets and translations.

    **Parameters:**

        source_obj
            The object from which the descendants will be copied.

        target_obj
            The object to which the descendants will be copied.
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

        source_obj
            The object from which the images will be copied.

        target_obj
            The object to which the images will be copied.
    """
    for image in source_obj.images.all():
        new_image = Image(content=target_obj, title=image.title)
        new_image.image.save(image.image.name, image.image.file, save=True)
        new_image.save()


def _copy_files(source_obj, target_obj):
    """Copies all files from source_obj to target_obj.

        source_obj
            The object from which the files will be copied.

        target_obj
            The object to which the files will be copied.
    """
    for file in source_obj.files.all():
        new_file = File(content=target_obj, title=file.title)
        new_file.file.save(file.file.name, file.file.file, save=True)
        new_file.save()


def _copy_portlets(source_obj, target_obj):
    """Copies all portlets from source_obj to target_obj.

        source_obj
            The object from which the portlets will be copied.

        target_obj
            The object to which the portlets will be copied.
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

        source_obj
            The object from which the translations will be copied.

        target_obj
            The object to which the translations will be copied.
    """
    for translation in source_obj.translations.all().get_content_objects():

        new_translation = copy.deepcopy(translation)
        new_translation.pk = None
        new_translation.id = None
        new_translation.slug = _generate_slug(translation, translation.parent)
        new_translation.canonical = target_obj

        amount = BaseContent.objects.filter(parent=translation.parent, language__in=("0", translation.language)).count()
        new_translation.position = (amount + 1) * 10
        new_translation.save()

        _copy_images(translation, new_translation)
        _copy_files(translation, new_translation)
        _copy_portlets(translation, new_translation)
        _copy_descendants(translation, new_translation)
