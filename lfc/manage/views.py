# python imports
import copy
import datetime

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
from django.utils import simplejson
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# tagging imports
from tagging.models import Tag

# portlets imports
from portlets.utils import get_registered_portlets
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
from lfc.manage.forms import CommentsForm
from lfc.manage.forms import ContentTypeRegistrationForm
from lfc.manage.forms import GroupForm
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
from lfc.settings import COPY, CUT
from lfc.utils import LazyEncoder
from lfc.utils import MessageHttpResponseRedirect
from lfc.utils import return_as_json
from lfc.utils import get_portal
from lfc.utils import import_module
from lfc.utils.registration import get_allowed_subtypes
from lfc.utils.registration import get_info

# Global #####################################################################
##############################################################################

@login_required
def add_object(request, language=None, id=None):
    """Adds a new content object to the object with the passed id. If the
    passed id is None the content object is added to the portal.
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

                new_object = form.save(commit=False)

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
                new_object.position = (amount+1) * 10

                new_object.save()

                # Send signal
                lfc.signals.post_content_added.send(new_object)

                # _update_positions(new_object, True)
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
        ctype = ContentType.objects.get_for_model(obj)
        parent = obj.parent
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

        obj.delete()

    if parent:
        url = reverse("lfc_manage_object", kwargs={"id": parent.id})
    else:
        url = reverse("lfc_manage_portal")

    msg = _(u"Page has been deleted.")
    return MessageHttpResponseRedirect(url, msg)

# Portal #####################################################################
##############################################################################

@login_required
def portal(request, template_name="lfc/manage/portal.html"):
    """Displays the main management screen of the portal with all tabs.
    """
    portal = get_portal()
    if not portal.has_permission(request.user, "manage_portal"):
        return lfc.utils.login_form()

    if settings.LFC_MANAGE_PERMISSIONS:
        permissions = portal_permissions(request)
    else:
        permissions = ""

    return render_to_response(template_name, RequestContext(request, {
        "menu" : portal_menu(request),
        "display_paste" : _display_paste(request),
        "core_data" : portal_core(request),
        "children" : portal_children(request),
        "portlets" : portlets_inline(request, get_portal()),
        "navigation" : navigation(request, None),
        "images" : portal_images(request, as_string=True),
        "files" : portal_files(request, as_string=True),
        "permissions" : permissions,
    }))

@login_required
def portal_permissions(request, template_name="lfc/manage/portal_permissions.html"):
    """Displays the permissions tab of the portal.
    """
    portal = get_portal()

    my_permissions = []
    for permission in Permission.objects.all():
        roles = []
        for role in Role.objects.all():
            roles.append({
                "id" : role.id,
                "name" : role.name,
                "has_permission" : _has_permission(portal, role, permission.codename),
            })

        my_permissions.append({
            "name" : permission.name,
            "codename" : permission.codename,
            "roles" : roles,
        })

    return render_to_string(template_name, RequestContext(request, {
        "roles" : Role.objects.all(),
        "permissions" : my_permissions,
    }))

def update_portal_permissions(request):
    """
    """
    obj = get_portal()

    permissions_dict = dict()
    for permission in request.POST.getlist("permission"):
        permissions_dict[permission] = 1

    for role in Role.objects.all():
        for permission in Permission.objects.all():
            perm_string = "%s|%s" % (role.id, permission.codename)
            if perm_string in permissions_dict:
                obj.grant_permission(role, permission)
            else:
                obj.remove_permission(role, permission)

    html = (
        ("#permissions", portal_permissions(request)),
    )

    result = simplejson.dumps({
        "html" : html,
        "message" : _(u"Permissions have been saved."),
    }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def portal_menu(request, template_name="lfc/manage/portal_menu.html"):
    """Displays the manage menu of the portal.
    """
    content_types = get_allowed_subtypes()
    return render_to_string(template_name, RequestContext(request, {
        "display_paste" : _display_paste(request),
        "display_content_menu" : len(get_allowed_subtypes()) > 1,
        "content_types" : get_allowed_subtypes(),
    }))

@login_required
def portal_core(request, template_name="lfc/manage/portal_core.html"):
    """Displays the core data tab of the portal.
    """
    portal = get_portal()

    if request.method == "POST":
        form = PortalCoreForm(instance=portal, data=request.POST)
        if form.is_valid():
            message = _(u"Portal data has been saved.")
            form.save()
        else:
            message = _(u"An error has been occured.")

        html =  render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "portal" : portal,
        }))

        html = (
            ("#data", html),
        )

        result = simplejson.dumps({
            "html" : html,
            "message" : message},
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
            "message" : _(u"Images have been added."),
        }, cls = LazyEncoder)

        return HttpResponse(result)

@login_required
def portal_files(request, as_string=False, template_name="lfc/manage/portal_files.html"):
    """Displays the files tab of the portal management screen.
    """
    obj = lfc.utils.get_portal()

    result = render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
    }))

    if as_string:
        return result
    else:
        result = simplejson.dumps({
            "files" : result,
            "message" : _(u"Files have been added."),
        }, cls = LazyEncoder)

        return HttpResponse(result)


# actions
def update_portal_children(request):
    """Deletes/Updates the children of the portal with passed ids (via
    request body).
    """
    portal = lfc.utils.get_portal()
    message = _update_children(request, portal)

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

def update_portal_images(request):
    """Updates images of the portal.
    """
    portal = lfc.utils.get_portal()
    message = _update_images(request, portal)

    result = simplejson.dumps({
        "images" : portal_images(request, as_string=True),
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

# @login_required
def add_portal_images(request):
    """Adds images to the portal.
    """
    obj = lfc.utils.get_portal()
    for file_content in request.FILES.values():
        image = Image(content=obj, title=file_content.name)
        image.image.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = (i+1) * 10
        image.save()

    return HttpResponse(portal_images(request, id, as_string=True))

# @login_required
def add_portal_files(request):
    """Addes files to the portal.
    """
    portal = lfc.utils.get_portal()
    for file_content in request.FILES.values():
        file = File(content=portal, title=file_content.name)
        file.file.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, file in enumerate(portal.files.all()):
        file.position = (i + 1) * 10
        file.save()

    return HttpResponse(portal_files(request))

@login_required
def update_portal_files(request):
    """Saves/deletes files for the portal.
    """
    portal = lfc.utils.get_portal()
    message = _update_files(request, portal)

    result = simplejson.dumps({
        "files" : portal_files(request, as_string=True),
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

# Objects ####################################################################
##############################################################################

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

    if not lfc.utils.registration.get_info(obj):
        raise Http404()

    if obj.has_permission(request.user, "view") == False:
         return HttpResponseRedirect(reverse("lfc_login"))

    if settings.LFC_MANAGE_PERMISSIONS:
        permissions = object_permissions(request, obj)
    else:
        permissions = ""

    return render_to_response(template_name, RequestContext(request, {
        "navigation" : navigation(request, obj),
        "menu" : object_menu(request, obj),
        "core_data" : object_core_data(request, id),
        "meta_data" : object_meta_data(request, id),
        "seo_data" : object_seo_data(request, id),
        "images" : object_images(request, id, as_string=True),
        "files" : object_files(request, id, as_string=True),
        "comments" : comments(request, obj),
        "portlets" : portlets_inline(request, obj),
        "children" : object_children(request, obj),
        "permissions" : permissions,
        "content_type_name" : get_info(obj).name,
        "display_paste" : _display_paste(request),
        "obj" : obj,
    }))

@login_required
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

    # Workflow
    transitions = obj.get_allowed_transitions(request.user)
    state = obj.get_state()

    return render_to_string(template_name, RequestContext(request, {
        "content_types" : content_types,
        "display_content_menu" : len(content_types) > 1,
        "translations" : translations,
        "languages" : languages,
        "canonical" : canonical,
        "obj" : obj,
        "display_paste" : _display_paste(request),
        "transitions" : transitions,
        "state" : state,
    }))

@login_required
def object_core_data(request, id, template_name="lfc/manage/object_data.html"):
    """Displays/Updates the core data tab of the content object with passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)
    obj_ct = ContentType.objects.filter(model=obj.content_type)[0]

    Form = obj.form

    if request.method == "POST":
        message = _("An error has been occured")

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

        html =  render_to_string(template_name, RequestContext(request, {
            "form" : form,
            "obj" : obj,
        }))

        html = (
            ("#core_data", html),
            ("#navigation", navigation(request, obj)),
        )

        result = simplejson.dumps({
            "html" : html,
            "message" : message,
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
def object_meta_data(request, id, template_name="lfc/manage/object_meta_data.html"):
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
def object_children(request, obj, template_name="lfc/manage/object_children.html"):
    """Displays the children of the passed content object.
    """
    return render_to_string(template_name, RequestContext(request, {
        "children" : obj.get_children(request),
        "obj" : obj,
        "display_paste" : _display_paste(request),
    }))

@login_required
def object_images(request, id, as_string=False, template_name="lfc/manage/object_images.html"):
    """Displays the images tab of a content object or a portal.
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
            "message" : _(u"Images have been added."),
        }, cls = LazyEncoder)

        return HttpResponse(result)

@login_required
def object_files(request, id, as_string=False, template_name="lfc/manage/object_files.html"):
    """Displays the files tab of the object with the passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)

    result = render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
    }))

    if as_string:
        return result
    else:
        result = simplejson.dumps({
            "files" : result,
            "message" : _(u"Files have been added."),
        }, cls = LazyEncoder)

        return HttpResponse(result)


@login_required
def object_seo_data(request, id, template_name="lfc/manage/object_seo.html"):
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
def object_permissions(request, obj, template_name="lfc/manage/object_permissions.html"):
    """Displays/Updates the permissions tab of the content object with passed id.
    """
    base_ctype = ContentType.objects.get_for_model(BaseContent)
    ctype = ContentType.objects.get_for_model(obj)

    workflow = obj.get_workflow()
    if workflow:
        wf_permissions = workflow.permissions.all()
    else:
        wf_permissions = []

    q = Q(content_types__in=(ctype, base_ctype)) | Q(content_types = None)
    my_permissions = []
    for permission in Permission.objects.filter(q):
        roles = []
        for role in Role.objects.all():
            roles.append({
                "id" : role.id,
                "name" : role.name,
                "has_permission" : _has_permission(obj, role, permission.codename),
            })

        my_permissions.append({
            "name" : permission.name,
            "codename" : permission.codename,
            "roles" : roles,
            "is_inherited" : obj.is_inherited(permission.codename),
            "is_wf_permission" : permission in wf_permissions,
        })

    return render_to_string(template_name, RequestContext(request, {
        "obj" : obj,
        "roles" : Role.objects.all(),
        "permissions" : my_permissions,
        "workflow" : workflow,
        "local_roles" : local_roles(request, obj),
    }))

@login_required
def local_roles(request, obj, template_name="lfc/manage/local_roles.html"):
    """
    """
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
        for role in Role.objects.all():

            roles.append({
                "id" : role.id,
                "name" : role.name,
                "has_local_role" : role in local_roles,
            })

        if user.first_name and user.last_name:
            name = "%s %s" % (user.first_name, user.last_name)
        else:
            name = user.username

        users.append({
            "id" : user.id,
            "name" : name,
            "roles" : roles,
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
        for role in Role.objects.all():

            roles.append({
                "id" : role.id,
                "name" : role.name,
                "has_local_role" : role in local_roles,
            })

        groups.append({
            "id" : group.id,
            "name" : group.name,
            "roles" : roles,
        })

    return render_to_string(template_name, RequestContext(request, {
        "users" : users,
        "groups" : groups,
        "roles" : Role.objects.all(),
        "obj" : obj,
    }))

def local_roles_add_form(request, id, template_name="lfc/manage/local_roles_add.html"):
    """Displays a form to add local roles to object with passed id.
    """
    return render_to_response(template_name, RequestContext(request, {
        "obj_id" : id,
    }))

def local_roles_search(request, id, template_name="lfc/manage/local_roles_search_result.html"):
    """
    """
    obj = lfc.utils.get_content_object(pk=id)
    ctype = ContentType.objects.get_for_model(obj)

    name = request.GET.get("name", "")
    q_users = Q(username__icontains=name) | Q(first_name__icontains=name) | Q(last_name__icontains=name)

    user_ids = [prr.user.id for prr in PrincipalRoleRelation.objects.exclude(user=None).filter(content_id=obj.id, content_type=ctype)]
    group_ids = [prr.group.id for prr in PrincipalRoleRelation.objects.exclude(group=None).filter(content_id=obj.id, content_type=ctype)]

    html = render_to_string(template_name, RequestContext(request, {
        "users" : User.objects.exclude(pk__in=user_ids).filter(q_users),
        "groups" : Group.objects.exclude(pk__in=group_ids).filter(name__icontains=name),
        "obj_id" : id,
        "roles" : Role.objects.all(),
    }))

    html = (
        ("#local-roles-search-result", html),
    )

    result = simplejson.dumps({
        "html" : html,
    }, cls = LazyEncoder)

    return HttpResponse(result)

# actions
@login_required
def add_local_roles(request, id):
    """
    """
    obj = lfc.utils.get_content_object(pk=id)
    ctype = ContentType.objects.get_for_model(obj)

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

    result = simplejson.dumps({
        "html" : html,
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

def save_local_roles(request, id):
    """
    """
    obj = lfc.utils.get_content_object(pk=id)
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

    result = simplejson.dumps({
        "html" : html,
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def update_object_children(request, id):
    """Deletes/Updates children for the content object with the passed id.The
    to updated children ids are passed within the request.
    """
    obj = lfc.utils.get_content_object(pk=id)
    message = _update_children(request, obj)

    _update_positions(obj)

    html = (
        ("#navigation", navigation(request, obj.get_content_object())),
        ("#children", object_children(request, obj)),
        ("#menu", object_menu(request, obj)),
    )

    result = simplejson.dumps({
        "html" : html,
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

def add_object_images(request, id):
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
        image.position = (i+1) * 10
        image.save()

    return HttpResponse(object_images(request, id, as_string=True))

@login_required
def update_object_images(request, id):
    """Saves/deletes images for content object with passed id or the portal
    (if id is None).

    The to deleted images are passed within the request body.
    """
    obj = lfc.utils.get_content_object(pk=id)
    message = _update_images(request, obj)

    result = simplejson.dumps({
        "images" : object_images(request, id, as_string=True),
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

def add_object_files(request, id):
    """Adds files to the content object with the passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)
    if request.method == "POST":
        for file_content in request.FILES.values():
            file = File(content=obj, title=file_content.name)
            file.file.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = (i + 1) * 10
        file.save()

    return HttpResponse(object_files(request, id))

@login_required
def update_object_files(request, id):
    """Saves/deletes files for the object with the passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)
    message = _update_files(request, obj)

    result = simplejson.dumps({
        "files" : object_files(request, id, as_string=True),
        "message" : message,
    }, cls = LazyEncoder)

    return HttpResponse(result)

def update_object_permissions(request, id):
    """Updates the permissions for the object with passed id.
    """
    obj = lfc.utils.get_content_object(pk=id)

    permissions_dict = dict()
    for permission in request.POST.getlist("permission"):
        permissions_dict[permission] = 1

    q = Q(content_types=obj) | Q(content_types = None)

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

    result = simplejson.dumps({
        "html" : html,
        "message" : _(u"Permissions have been saved."),
    }, cls = LazyEncoder)

    return HttpResponse(result)

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
        "obj" : obj,
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

    html = (
        ("#portlets", portlets_inline(request, obj)),
    )

    result = simplejson.dumps({
        "html" : html,
        "message" : _(u"Portlets have been updated.")},
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

    temp = lfc.utils.get_content_objects(request, q)

    objs = []
    for obj in temp:
        obj = obj.get_content_object()

        if obj.has_permission(request.user, "view") == False:
            continue

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

        if not lfc.utils.registration.get_info(obj):
            continue

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
@login_required
def set_navigation_tree_language(request, language):
    """Sets the language for the navigation tree.
    """
    request.session["nav-tree-lang"] = language
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

def set_language(request, language):
    """Sets the language of the portal.
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

@login_required
def comments(request, obj, template_name="lfc/manage/object_comments.html"):
    """Displays the comments tab of the passed object.
    """
    form = CommentsForm(instance=obj)
    comments = Comment.objects.filter(object_pk = str(obj.id))

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

# Filebrowser ################################################################
##############################################################################

def filebrowser(request):
    """Displays files/images of the current object within the file browser
    popup of TinyMCE.
    """
    obj_id = request.GET.get("obj_id")

    try:
        obj = lfc.utils.get_content_object(pk=obj_id)
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
        portal = lfc.utils.get_portal()
        if obj:
            local_files = obj.files.all()
            global_files = portal.files.all()
        else:
            local_files = []
            global_files = obj.files.all()
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
            "local_files" : local_files,
            "global_files" : global_files,
            "objs" : base_contents,
        }))

def _filebrowser_children(request, obj):
    """
    """
    objs = []
    for obj in obj.get_children(request):
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
    obj = lfc.utils.get_content_object(pk=obj_id)

    if request.method == "POST":
        for file_content in request.FILES.values():
            image = Image(content=obj, title=file_content.name)
            image.image.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, image in enumerate(obj.images.all()):
        image.position = (i+1) * 10
        image.save()

    url = "%s?obj_id=%s&amp;type=image" % (reverse("lfc_filebrowser"), obj_id)
    return HttpResponseRedirect(url)

def fb_upload_file(request):
    """Uploads file within filebrowser.
    """
    obj_id = request.POST.get("obj_id")
    obj = lfc.utils.get_content_object(pk=obj_id)

    for file_content in request.FILES.values():
        file = File(content=obj, title=file_content.name)
        file.file.save(file_content.name, file_content, save=True)

    # Refresh positions
    for i, file in enumerate(obj.files.all()):
        file.position = (i+1) * 10
        file.save()

    url = "%s?obj_id=%s" % (reverse("lfc_filebrowser"), obj_id)
    return HttpResponseRedirect(url)

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

# Template ###################################################################
##############################################################################

@login_required
def set_template(request):
    """Sets the template of the current object
    """
    obj_id = request.POST.get("obj_id")
    template_id = request.POST.get("template_id")

    obj = BaseContent.objects.get(pk=obj_id)
    obj.template_id = template_id
    obj.save()

    return HttpResponseRedirect(obj.get_absolute_url())

# Review objects #############################################################
##############################################################################

@login_required
def review_objects(request, template_name="lfc/manage/review_objects.html"):
    """Displays a list of submitted objects.
    """
    portal = get_portal()

    review_states = [wst.state for wst in WorkflowStatesInformation.objects.filter(review=True)]

    objs = []
    for obj in lfc.utils.get_content_objects():
        if obj.get_state() in review_states:
            objs.append(obj)

    return render_to_response(template_name, RequestContext(request, {
        "objs" : objs,
    }))

# Workflow ###################################################################
##############################################################################

@login_required
def do_transition(request, id):
    """Processes passed transition for object with passed id.
    """
    transition = request.REQUEST.get("transition")
    try:
        transition = Transition.objects.get(pk=transition)
    except Transition.DoesNotExist:
        pass
    else:
        obj = lfc.utils.get_content_object(pk=id)
        workflows.utils.do_transition(obj, transition, request.user)

        # Set publication date
        if obj.publication_date is None:
            public_states = [wst.state for wst in WorkflowStatesInformation.objects.filter(public=True)]
            if obj.get_state() in public_states:
                obj.publication_date = datetime.datetime.now()
                obj.save()

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

@login_required
def manage_workflow(request, id=None, template_name="lfc/manage/workflow.html"):
    """Main page to manage a workflow.
    """
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
                reverse("lfc_manage_workflow", kwargs={"id" : workflow.id }))

    return render_to_response(template_name, RequestContext(request, {
        "data" : workflow_data(request, workflow),
        "states" : workflow_states(request, workflow),
        "transitions" : workflow_transitions(request, workflow),
        "menu" : workflow_menu(request, workflow),
        "navigation" : workflow_navigation(request, workflow),
        "workflow" : workflow,
    }))

@login_required
def workflow_data(request, workflow, template_name="lfc/manage/workflow_data.html"):
    """Displays the data tab of the workflow with passed workflow.
    """
    form = WorkflowForm(instance=workflow)

    selected = [w.permission for w in WorkflowPermissionRelation.objects.filter(workflow=workflow)]

    permissions = []
    for permission in Permission.objects.all():
        permissions.append({
            "id" : permission.id,
            "name" : permission.name,
            "checked" : permission in selected,
        })

    return render_to_string(template_name, RequestContext(request, {
        "workflow" : workflow,
        "form" : form,
        "permissions" : permissions,
    }))

@login_required
def workflow_states(request, workflow, template_name="lfc/manage/workflow_states.html"):
    """Displays the states tab of the passed workflow.
    """
    return render_to_string(template_name, RequestContext(request, {
        "workflow" : workflow,
    }))

@login_required
def workflow_transitions(request, workflow, template_name="lfc/manage/workflow_transitions.html"):
    """Displays the transitions tab of the passed workflow.
    """
    return render_to_string(template_name, RequestContext(request, {
        "workflow" : workflow,
    }))

@login_required
def workflow_menu(request, workflow=None, template_name="lfc/manage/workflow_menu.html"):
    """Displays the horizontal menu of the workflow
    """
    return render_to_string(template_name, RequestContext(request, {
        "workflow" : workflow,
    }))

@login_required
def workflow_navigation(request, workflow=None, template_name="lfc/manage/workflow_navigation.html"):
    """Displays the left side navigation of a workflow
    """
    return render_to_string(template_name, RequestContext(request, {
        "current_workflow" : workflow,
        "workflows" : Workflow.objects.all()
    }))

# actions
@login_required
def save_workflow_data(request, id):
    """Saves the workflow data.
    """
    workflow = Workflow.objects.get(pk=id)

    form = WorkflowForm(instance=workflow, data=request.POST)
    if form.is_valid:
        form.save()

    selected = request.POST.getlist("permission")

    for permission in Permission.objects.all():
        if str(permission.id) in selected:
            try:
                WorkflowPermissionRelation.objects.create(workflow=workflow, permission=permission)
            except IntegrityError:
                pass
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

@login_required
def add_workflow(request, template_name="lfc/manage/workflow_add.html"):
    """Displays an add form and adds a workflow.
    """
    if request.method == "POST":
        form = WorkflowAddForm(data = request.POST)
        if form.is_valid():
            workflow = form.save()
            return MessageHttpResponseRedirect(
                reverse("lfc_manage_workflow", kwargs = {"id" : workflow.id }),
                _(u"Workflow has been added."))
    else:
        form = WorkflowAddForm()

    return render_to_response(template_name, RequestContext(request, {
        "form" : form,
        "menu" : workflow_menu(request),
        "navigation" : workflow_navigation(request),
    }))

@login_required
def delete_workflow(request, id):
    """
    """
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

# Workflow state #############################################################
##############################################################################
@login_required
def manage_state(request, id, template_name="lfc/manage/workflow_state.html"):
    """Manages a single workflow state.
    """
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
                "id" : role.id,
                "name" : role.name,
                "checked" : checked,
            })

        try:
            StateInheritanceBlock.objects.get(state=state, permission=permission)
        except StateInheritanceBlock.DoesNotExist:
            inherited = True
        else:
            inherited = False

        permissions.append({
            "id" : permission.id,
            "name" : permission.name,
            "roles" : roles_temp,
            "inherited" : inherited,
        })

    try:
        wsi = WorkflowStatesInformation.objects.get(state=state)
    except WorkflowStatesInformation.DoesNotExist:
        public = False
        review = False
    else:
        public = wsi.public
        review = wsi.review

    return render_to_response(template_name, RequestContext(request, {
        "state" : state,
        "form" : form,
        "permissions" : permissions,
        "roles" : roles,
        "public" : public,
        "review" : review,
    }))

@login_required
def save_workflow_state(request, id):
    """Saves the workflow state with passed id.
    """
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

    for role in Role.objects.all():
        for permission in Permission.objects.all():

            # Inheritance
            if str(permission.id) in inherited_ids:
                try:
                    sib = StateInheritanceBlock.objects.get(state=state, permission=permission)
                except StateInheritanceBlock.DoesNotExist:
                    pass
                else:
                    sib.delete()
            else:
                StateInheritanceBlock.objects.get_or_create(state=state, permission=permission)

            # Roles
            role_permission_id  = "%s|%s" % (role.id, permission.id)
            if role_permission_id in role_permssion_ids:
                StatePermissionRelation.objects.get_or_create(state=state, role=role, permission=permission)
            else:
                try:
                    spr = StatePermissionRelation.objects.get(state=state, role=role, permission=permission)
                except StatePermissionRelation.DoesNotExist:
                    pass
                else:
                    spr.delete()

    html = (
        ("#data", workflow_data(request, state.workflow)),
        ("#states", workflow_states(request, state.workflow)),
    )

    return return_as_json(html, _(u"State has been saved."))

@login_required
def add_workflow_state(request, id):
    """
    """
    name = request.POST.get("name")
    if name != "":
        state = State.objects.create(workflow_id = id, name=name)

    html = (
        ("#data", workflow_data(request, state.workflow)),
        ("#states", workflow_states(request, state.workflow)),
    )

    return return_as_json(html, _(u"State has been added."))

@login_required
def delete_workflow_state(request, id):
    """Deletes the transition with passed id.
    """
    try:
        state = State.objects.get(pk=id)
    except State.DoesNotExist:
        pass
    else:
        if state.workflow.get_initial_state() == state:
            state.workflow.initial_state = None
            state.workflow.save()
        state.delete()

    return MessageHttpResponseRedirect(
        request.META.get("HTTP_REFERER"), _(u"State has been deleted.")
    )

# Workflow transition ########################################################
##############################################################################
@login_required
def manage_transition(request, id, template_name="lfc/manage/workflow_transition.html"):
    """Manages transition with passed id.
    """
    transition = Transition.objects.get(pk=id)
    form = TransitionForm(instance=transition)

    return render_to_response(template_name, RequestContext(request, {
        "transition" : transition,
        "form" : form,
    }))

@login_required
def save_workflow_transition(request, id):
    """Saves the workflow state with passed id.
    """
    transition = Transition.objects.get(pk=id)

    form = TransitionForm(instance=transition, data=request.POST)
    if form.is_valid:
        form.save()

    html = (
        ("#transitions", workflow_transitions(request, transition.workflow)),
        ("#states", workflow_states(request, transition.workflow)),
    )

    return return_as_json(html, _(u"Transition has been saved."))

@login_required
def add_workflow_transition(request, id):
    """Adds a transition to workflow with passed id.
    """
    workflow = Workflow.objects.get(pk=id)

    name = request.POST.get("name")
    if name != "":
        state = Transition.objects.create(workflow = workflow, name=name)

    html = (
        ("#transitions", workflow_transitions(request, workflow)),
    )

    return return_as_json(html, _(u"Transition has been added."))

@login_required
def delete_workflow_transition(request, id):
    """Deletes the transition with passed id.
    """
    try:
        transition = Transition.objects.get(pk=id)
    except Transition.DoesNotExist:
        pass
    else:
        transition.delete()

    return MessageHttpResponseRedirect(
        request.META.get("HTTP_REFERER"), _(u"Transition has been deleted.")
    )

# Cut/Copy and paste #########################################################
##############################################################################

@login_required
def lfc_copy(request, id):
    """Puts the object with passed id into the clipboard.
    """
    request.session["clipboard"] = [id]
    request.session["clipboard_action"] = COPY

    url = reverse("lfc_manage_object", kwargs = { "id" : id })
    msg = _(u"The object has been put to the clipboard.")

    return MessageHttpResponseRedirect(url, msg)

@login_required
def cut(request, id):
    """Puts the object within passed id into the clipboard and marks action
    as cut.
    """
    request.session["clipboard"] = [id]
    request.session["clipboard_action"] = CUT

    url = reverse("lfc_manage_object", kwargs = { "id" : id })
    msg = _(u"The object has been put to the clipboard.")

    return MessageHttpResponseRedirect(url, msg)

@login_required
def paste(request, id=None):
    """Paste the object in the clipboard to object with given id.
    """
    if id:
        url = reverse("lfc_manage_object", kwargs = { "id" : id })
        obj = lfc.utils.get_content_object(pk=id)
    else:
        url = reverse("lfc_manage_portal")
        obj = None

    msg = _paste(request, obj)
    return MessageHttpResponseRedirect(url, msg)

def _paste(request, obj):
    """
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

            # _copy_images(source_obj, target_obj)
            # _copy_files(source_obj, target_obj)
            # _copy_portlets(source_obj, target_obj)
            # _copy_translations(source_obj, target_obj)

            # Prevent recursion
            if target not in descendants and target != source_obj:
                _copy_descendants(source_obj, target_obj)

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

        amount = BaseContent.objects.filter(parent=translation.parent, language__in=("0", translation.language)).count()
        new_translation.position = (amount + 1) * 10
        new_translation.save()

        _copy_images(translation, new_translation)
        _copy_files(translation, new_translation)
        _copy_portlets(translation, new_translation)
        _copy_descendants(translation, new_translation)

# Content types ##############################################################
##############################################################################

@login_required
def content_types(request):
    """Redirects to the first content type.
    """
    ctr = ContentTypeRegistration.objects.filter()[0]
    url = reverse("lfc_content_type", kwargs={"id" : ctr.id })
    return HttpResponseRedirect(url)

@login_required
def content_type(request, id, template_name="lfc/manage/content_types.html"):
    """ Displays the main screen of the content type management.
    """
    ctr = ContentTypeRegistration.objects.get(pk=id)
    ctype = ContentType.objects.get(model = ctr.type)

    old_workflow = ctr.workflow

    if old_workflow:
        old_objects = old_workflow.get_objects()
    else:
        old_objects = []

    message = ""
    if request.method == "POST":
        form = ContentTypeRegistrationForm(data = request.POST, instance=ctr)
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
        "types" : ContentTypeRegistration.objects.all(),
        "ctr" : ctr,
        "form" : form,
    }))

    return lfc.utils.set_message_to_reponse(response, message)

# Applications ###############################################################
##############################################################################

@login_required
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

    return render_to_response(template_name, RequestContext(request, {
        "applications" : applications,
    }))

@login_required
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

@login_required
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

@login_required
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

# Users ######################################################################
##############################################################################
@login_required
def manage_users(request, template_name="lfc/manage/users.html"):
    """
    """
    return render_to_response(template_name, RequestContext(request, {
        "users" : users_inline(request),
    }))

@login_required
def users_inline(request, template_name="lfc/manage/users_inline.html"):
    """
    """
    users = _get_filtered_users(request, "users")
    paginator = Paginator(users, 20)
    p = request.session.get("page", request.REQUEST.get("page", 1))

    try:
        page = paginator.page(p)
    except EmptyPage:
        page = 0

    return render_to_string(template_name, RequestContext(request, {
        "users" : users,
        "paginator" : paginator,
        "page" : page,
        "name_filter" : request.session.get("users_name_filter", ""),
        "active_filter" : request.session.get("users_active_filter", "")
    }))

@login_required
def change_users(request):
    """Updates or deletes checked users.
    """
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

    result = simplejson.dumps(
        { "html" : html, "message" : message, }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def set_users_page(request):
    """Sets the current user page.
    """
    request.session["users_page"] = request.GET.get("page", 1)

    user = request.GET.get("user")
    if user:
        html = (("#navigation", user_navigation(request, user)), )
    else:
        html = (("#users", users_inline(request)), )

    result = simplejson.dumps({ "html" : html }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def set_users_filter(request):
    """Filter users
    """
    _update_filter(request, "users_active_filter")
    _update_filter(request, "users_name_filter")
    request.session["users_page"] = 1

    message = _(u"Filter has been set.")
    html = (("#users", users_inline(request)), )

    result = simplejson.dumps(
        { "html" : html, "message" : message, }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def reset_users_filter(request):
    """
    """
    _delete_filter(request, "users_name_filter")
    _delete_filter(request, "users_active_filter")
    _delete_filter(request, "users_page")

    message = _(u"Filter has been reset.")

    user = request.GET.get("user")
    if user:
        html = (("#navigation", user_navigation(request, user)), )
    else:
        html = (("#users", users_inline(request)), )

    result = simplejson.dumps(
        { "html" : html, "message" : message, }, cls = LazyEncoder)

    return HttpResponse(result)

# User #######################################################################
##############################################################################

@login_required
def manage_user(request, id=None, template_name="lfc/manage/user.html"):
    """Displays main screen to manage the user with passed id.
    """
    if id is None:
        user = User.objects.all()[0]
        return HttpResponseRedirect(reverse("lfc_manage_user", kwargs={ "id" : user.id }))

    result = render_to_response(template_name, RequestContext(request, {
        "data" : user_data(request, id),
        "password" : user_password(request, id),
        "menu" : user_menu(request, id),
        "navigation" : user_navigation(request, id),
        "current_user_id" : id,
        "user_name_filter" : request.session.get("user_name_filter", "")
    }))

    return HttpResponse(result)

@login_required
def user_menu(request, id, template_name="lfc/manage/user_menu.html"):
    """Displays the menu within user management.
    """
    return render_to_string(template_name, RequestContext(request, {
        "current_user_id" : id,
        "display_delete" : id != "1",
    }))

@login_required
def user_data(request, id, template_name="lfc/manage/user_data.html"):
    """Displays the user data form of the user with passed id.
    """
    user = User.objects.get(pk=id)

    if request.method == "POST":
        form = UserForm(instance=user, data=request.POST)
    else:
        form = UserForm(instance=user)

    return render_to_string(template_name, RequestContext(request, {
        "myuser" : user,
        "form" : form,
    }))

@login_required
def user_password(request, id, form=None, template_name="lfc/manage/user_password.html"):
    """Displays the change password form of the user with passed id.
    """
    user = User.objects.get(pk=id)

    if request.method == "POST":
        form = AdminPasswordChangeForm(user, request.POST)
    else:
        form = AdminPasswordChangeForm(user)

    return render_to_string(template_name, RequestContext(request, {
        "form" : form,
    }))

@login_required
def user_navigation(request, id, template_name="lfc/manage/user_navigation.html"):
    """Displays the user navigation.
    """
    users = _get_filtered_users(request, "user")
    paginator = Paginator(users, 30)
    page = request.session.get("user_page", request.REQUEST.get("page", 1))

    try:
        page = paginator.page(page)
    except EmptyPage:
        page = 0

    return render_to_string(template_name, RequestContext(request, {
        "current_user_id" : int(id),
        "paginator" : paginator,
        "page" : page,
    }))

# actions
@login_required
def save_user_data(request, id):
    """Saves the user data form of the user with the passed id.
    """
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

    result = simplejson.dumps(
        { "html" : html, "message" : message, }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def change_password(request, id):
    """
    """
    user = User.objects.get(pk=id)
    form = AdminPasswordChangeForm(user, request.POST)

    if form.is_valid():
        form.save()
        message = _(u"Password has been changed")
    else:
        message = _(u"An error occured.")

    html = (("#password", user_password(request, id, form)), )

    result = simplejson.dumps(
        { "html" : html, "message" : message, }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def add_user(request, template_name="lfc/manage/user_add.html"):
    """Displays a add user form.
    """
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

            url = reverse("lfc_manage_user", kwargs={"id" : user.id})
            message = _(u"User has been added")
            return MessageHttpResponseRedirect(url, message)

        else:
            return render_to_response(template_name, RequestContext(request, {
                "form" : form,
                "navigation" : user_navigation(request, 0),
            }))
    else:
        form = UserAddForm()
        return render_to_response(template_name, RequestContext(request, {
            "form" : form,
            "navigation" : user_navigation(request, 0),
        }))

@login_required
def delete_user(request, id):
    """
    """
    try:
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        pass
        message = _(u"User couldn't deleted.")
    else:
        user.delete()
        message = _(u"User has been deleted.")

    user = User.objects.all()[0]
    url = reverse("lfc_manage_user", kwargs={"id" : user.id })
    return MessageHttpResponseRedirect(url, message)

@login_required
def set_user_page(request):
    """Sets the current user page.
    """
    request.session["user_page"] = request.GET.get("page", 1)
    user = request.GET.get("user")

    html = (("#navigation", user_navigation(request, user)), )
    result = simplejson.dumps({ "html" : html }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def set_user_filter(request):
    """Filter users
    """
    user = request.GET.get("user")

    _update_filter(request, "user_name_filter")
    request.session["user_page"] = 1

    html = (("#navigation", user_navigation(request, user)), )

    result = simplejson.dumps(
        { "html" : html }, cls = LazyEncoder)

    return HttpResponse(result)

@login_required
def reset_user_filter(request):
    """
    """
    _delete_filter(request, "user_name_filter")
    _delete_filter(request, "user_page")

    message = _(u"Filter has been reset.")

    user = request.GET.get("user")
    html = (("#navigation", user_navigation(request, user)), )

    result = simplejson.dumps(
        { "html" : html, "message" : message, }, cls = LazyEncoder)

    return HttpResponse(result)

# Group ######################################################################
# ############################################################################

@login_required
def manage_group(request, id=None, template_name="lfc/manage/group.html"):
    """
    """
    if id is None:
        try:
            id = Group.objects.all()[0].id
            return HttpResponseRedirect(reverse("lfc_manage_group", kwargs={"id" : id}))
        except IndexError:
            return HttpResponseRedirect(reverse("lfc_manage_add_group"))

    group = Group.objects.get(pk=id)

    form = GroupForm(instance=group)
    return render_to_response(template_name, RequestContext(request, {
        "form" : form,
        "group" : group,
        "groups" : Group.objects.all(),
        "current_group_id" : group.id,
    }))

@login_required
def add_group(request, template_name="lfc/manage/group_add.html"):
    """Displays a add group form.
    """
    if request.method == "POST":
        form = GroupForm(data=request.POST)
        if form.is_valid():
            group = form.save()
            return HttpResponseRedirect(reverse("lfc_manage_group", kwargs={"id" : group.id}))
        else:
            return render_to_response(template_name, RequestContext(request, {
                "form" : form,
                "groups" : Group.objects.all(),
            }))
    else:
        form = GroupForm()
        return render_to_response(template_name, RequestContext(request, {
            "form" : form,
            "groups" : Group.objects.all(),
        }))

@login_required
def delete_group(request, id, template_name="lfc/manage/group_add.html"):
    """Deletes a group.
    """
    try:
        Group.objects.get(pk=id).delete()
    except Group.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse("lfc_manage_group"))

@login_required
def save_group(request, id, template_name="lfc/manage/group_add.html"):
    """Saves group with passed id.
    """
    group = Group.objects.get(pk=id)
    form = GroupForm(instance=group, data=request.POST)
    if form.is_valid():
        group = form.save()
        return HttpResponseRedirect(reverse("lfc_manage_group", kwargs={"id" : group.id}))
    else:
        return render_to_response(template_name, RequestContext(request, {
            "form" : form,
            "group" : group,
            "groups" : Group.objects.all(),
            "current_group_id" : int(id),
        }))

# Roles ######################################################################
# ############################################################################

@login_required
def manage_role(request, id=None, template_name="lfc/manage/role.html"):
    """Displays manage interface for role with passed id.
    """
    if id is None:
        try:
            role = Role.objects.exclude(name__in=("Anonymous", "Owner"))[0]
        except IndexError:
            return HttpResponseRedirect(reverse("lfc_manage_add_role"))
        else:
            return HttpResponseRedirect(reverse("lfc_manage_role", kwargs={"id" : role.id}))

    role = Role.objects.get(pk=id)
    if role.name in ["Anonymous", "Owner"]:
        raise Http404

    form = RoleForm(instance=role)

    return render_to_response(template_name, RequestContext(request, {
        "form" : form,
        "role" : role,
        "roles" : Role.objects.exclude(name__in = ("Anonymous", "Owner")),
        "current_role_id" : int(id),
    }))

@login_required
def add_role(request, template_name="lfc/manage/role_add.html"):
    """Displays a add role form.
    """
    if request.method == "POST":
        form = RoleForm(data=request.POST)
        if form.is_valid():
            role = form.save()
            return HttpResponseRedirect(reverse("lfc_manage_role", kwargs={"id" : role.id}))
        else:
            return render_to_response(template_name, RequestContext(request, {
                "form" : form,
            }))
    else:
        form = RoleForm()
        return render_to_response(template_name, RequestContext(request, {
            "form" : form,
            "roles" : Role.objects.exclude(name__in = ("Anonymous", "Owner")),
        }))

@login_required
def delete_role(request, id, template_name="lfc/manage/role_add.html"):
    """Deletes a role.
    """
    try:
        Role.objects.get(pk=id).delete()
    except Role.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse("lfc_manage_role"))

@login_required
def save_role(request, id, template_name="lfc/manage/role_add.html"):
    """Saves role with passed id.
    """
    role = Role.objects.get(pk=id)
    form = RoleForm(instance=role, data=request.POST)
    if form.is_valid():
        role = form.save()
        return HttpResponseRedirect(reverse("lfc_manage_role", kwargs={"id" : role.id}))
    else:
        return render_to_response(template_name, RequestContext(request, {
            "form" : form,
            "role" : role,
            "roles" : Role.objects.exclude(name__in = ("Anonymous", "Owner")),
            "current_role_id" : int(id),
        }))

# Privates ###################################################################
##############################################################################

def _get_filtered_users(request, prefix):
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
    if request.session.has_key(name):
        del request.session[name]

def _update_filter(request, name):
    filter = request.GET.get(name, "")
    if filter != "":
        request.session[name] = filter
    else:
        if request.session.has_key(name):
            del request.session[name]

def _update_children(request, obj):
    """Updates the children of the passed object. Returns a message which can
    be displayed to the user.
    """
    action = request.POST.get("action")
    if action == "delete":
        message = _(u"Objects has been deleted.")
        for key in request.POST.keys():
            if key.startswith("delete-"):
                try:
                    id = key.split("-")[1]
                    child = lfc.utils.get_content_object(pk=id)
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

        if isinstance(obj, Portal):
            _update_positions(None)
        else:
            _update_positions(obj)

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

def _display_paste(request):
    """Returns true if the paste button should be displayed.
    """
    return request.session.has_key("clipboard")

def _remove_fks(obj):
    """Removes the objects from foreign key fields (in order to not delete
    these related objects)
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
            objs = BaseContent.objects.filter(parent=parent, language = language[0])

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
        content_type=ct, content_id=obj.id, role=role, permission__codename = codename)

    if p.count() > 0:
        return True
    return False
