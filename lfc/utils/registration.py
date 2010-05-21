# django imports
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

# lfc imports
from lfc.models import BaseContent
from lfc.models import ContentTypeRegistration
from lfc.models import Portal
from lfc.models import Template

# workflow imports
from workflows.models import Workflow
from workflows.models import WorkflowModelRelation

def get_info(obj_or_type):
    """Returns the ContentTypeRegistration for the passed object or type.
    Returns None if the content type registry is not found.

    **Parameters:**

    obj_or_type
        The object or type for which the information should be returned. Must
        be an instance of BaseContent or a String with a valid type name.

    """
    if isinstance(obj_or_type, BaseContent):
        type = obj_or_type.__class__.__name__.lower()
    else:
        type = obj_or_type

    # CACHE
    cache_key = "info-%s" % type
    result = cache.get(cache_key)
    if result:
        return result

    try:
        result = ContentTypeRegistration.objects.get(type = type)
    except ContentTypeRegistration.DoesNotExist:
        result = None

    # Set cache
    cache.set(cache_key, result)

    return result

def get_allowed_subtypes(obj_or_type=None):
    """Returns all allowed sub types for given object or type. Returns a list
    of ContentTypeRegistrations.

    **Parameters:**

    obj_or_type
        Must be an instance of BaseContent, a string with a valid type name or
        None. If it's None the conten type registrations of all global addable
        content types are returned.
    """
    if obj_or_type is None or isinstance(obj_or_type, Portal):
        return ContentTypeRegistration.objects.filter(global_addable=True)

    ctr = get_info(obj_or_type)
    if ctr:
        return ctr.get_subtypes()
    else:
        return []

def register_sub_type(klass, name):
    """Registers a content type as a allowed sub type to another content type.

    **Parameters:**

    klass
        The class which should be registered.

    name
        The name of the content type to which the passed content type (klass)
        should be registered.
    """
    try:
        base_ctr = ContentTypeRegistration.objects.get(name=name)
    except ContentTypeRegistration.DoesNotExist:
        return

    sub_ctr = get_info(klass.__name__.lower())

    if sub_ctr:
        base_ctr.subtypes.add(sub_ctr)

def register_content_type(klass, name, sub_types=[], templates=[], default_template=None, global_addable=True, workflow=None):
    """Registers a content type.

    **Parameters:**

    klass
        The klass which should be registered as content type. Must be a sub
        class of BaseContent.

    name
        The unique name under which the content type should be registered.

    sub_types
        Content types which are allowed to be added as children to the
        registered object. Must be a list of strings with valid names of
        content types.

    templates
        Templates which are allowed to be selected for the registered object.
        Must be a list of strings with valid template names.

    default_template
        Default template of the registered object.

    global_addable
        Decides whether the content type is global addable or just within
        specific content types.

    Workflow
        The workflow of the content type. Needs to be a string with the
        unique workflow name.
    """
    type = klass.__name__.lower()
    try:
        ctr, created = ContentTypeRegistration.objects.get_or_create(type=type, name=name)
        ctr.save()
    except:
        pass
    else:
        # Don't update a content type for now
        if created:
            # Set attributes
            ctr.global_addable = global_addable
            ctr.save()

            # Add subtypes
            for sub_type in sub_types:
                try:
                    sub_ctr = ContentTypeRegistration.objects.get(type = sub_type.lower())
                except ContentTypeRegistration.DoesNotExist:
                    pass
                else:
                    ctr.subtypes.add(sub_ctr)

            # Add templates and default template
            for template_name in templates:
                try:
                    template = Template.objects.get(name = template_name)
                except Template.DoesNotExist:
                    pass
                else:
                    ctr.templates.add(template)
                    if template_name == default_template:
                        ctr.default_template = template
                        ctr.save()

            # Add workflow
            if workflow:
                try:
                    wf = Workflow.objects.get(name=workflow)
                except Workflow.DoesNotExist:
                    pass
                else:
                    ctr.workflow = wf
                    ctr.save()

                    ctype = ContentType.objects.get_for_model(klass)
                    try:
                        wmr = WorkflowModelRelation.objects.get(content_type=ctype)
                    except WorkflowModelRelation.DoesNotExist:
                        WorkflowModelRelation.objects.create(workflow=wf, content_type=ctype)
                    else:
                        wmr.content_type = ctype
                        wmr.save()

def unregister_content_type(name):
    """Unregisteres content type with passed name.
    """

    # Remove Workflow Model Relation
    try:
        ctype = ContentType.objects.get(name=name.lower())
        wmr = WorkflowModelRelation.objects.get(content_type=ctype)
    except ObjectDoesNotExist:
        pass
    else:
        wmr.delete()

    # Remove ContentType
    try:
        ctr = ContentTypeRegistration.objects.get(name=name)
    except ContentTypeRegistration.DoesNotExist:
        pass
    else:
        ctr.delete()

def register_template(name, path, children_columns=0, images_columns=0):
    """Registers a template.

    **Parameters:**

    name
        The name of the template.

    path
        The path to the template file.

    children_columns
        The amount of columns for sub pages. This can be used within templates
        to structure children.

    images_columns
        The amount of columns for images. This can be used within templates
        to structure images.
    """
    try:
        name = name._proxy____str_cast()
    except AttributeError:
        pass
    try:
        Template.objects.create(name = name, path=path,
            children_columns=children_columns, images_columns=images_columns)
    except IntegrityError:
        pass

def unregister_template(name):
    """Unregisters the template with the given name.

    **Parameters:**

    name
        The name of the template.
    """
    try:
        template = Template.objects.get(name = name)
    except Template.DoesNotExist:
        pass
    else:
        template.delete()

def get_default_template(obj_or_type):
    """Returns the default template for given object or type. Returns an
    instance of Template.

    **Parameters:**

    obj_or_type
        The object or type for which the temlate should be returned. Must be
        an instance of BaseContent or a String with a valid type name.
    """
    ctr = get_info(obj_or_type)
    if ctr is None:
        return None
    else:
        return ctr.default_template

def get_templates(obj_or_type):
    """Returns allowed templates for passed object or type.

    **Parameters:**

    obj_or_type
        The object or type for which the temlates should be returned. Must be
        an instance of BaseContent or a String with a valid type name. Returns
        a list of Template instances.
    """
    ctr = get_info(obj_or_type)
    if ctr is None:
        return []
    else:
        return ctr.get_templates()
