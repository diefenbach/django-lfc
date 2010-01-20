# lfc imports
from lfc.models import ContentTypeRegistration
from lfc.models import Template
from lfc.models import BaseContent

# django imports
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

def get_info_for(obj_or_type):
    """Returns the ContentTypeRegistration for the passed object or type.
    Returns None if the content type registry is not found.

    **Parameters:**

    obj_or_type
        Must be an instance of BaseContent or a String with a valid type name.

    """
    if isinstance(obj_or_type, BaseContent):
        type = obj_or_type.__class__.__name__.lower()
    else:
        type = obj_or_type

    try:
        return ContentTypeRegistration.objects.get(type = type)
    except ContentTypeRegistration.DoesNotExist:
        return None

def get_allowed_subtypes(obj_or_type=None):
    """Returns all allowed sub types for given object.

    **Parameters:**

    obj_or_type
        Must be an instance of BaseContent, a String with a valid type name or
        None. If it's None the conten type registrations of all global addable
        content types are returned.
    """
    if obj_or_type is None:
        return ContentTypeRegistration.objects.filter(global_addable=True)

    ctr = get_info_for(obj_or_type)
    if ctr:
        return ctr.subtypes.all()
    else:
        return []

def register_sub_type(klass, name):
    """Registers the content type klass as allowed content type name.

    **Parameters:**

    klass
        The class which should be registered as valid sub type to an content
        type.

    name
        The name of the content type to which klass should be registered.
    """
    try:
        base_ctr = ContentTypeRegistration.objects.get(name=name)
    except ContentTypeRegistration.DoesNotExist:
        return

    sub_ctr = get_info_for(klass.__name__.lower())

    if sub_ctr:
        base_ctr.subtypes.add(sub_ctr)

def register_content_type(klass, name, sub_types=[], templates=[], default_template=None):
    """Registers passed object as a content type.

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

def register_template(name, path, subpages_columns=0, images_columns=0):
    """Registers a template.

    **Parameters:**

    name
        The name of the template.

    path
        The path to the template file.

    subpages_columns
        The amount of columns for sub pages.

    images_columns
        The amount of columns for images.
    """
    try:
        name = name._proxy____str_cast()
    except AttributeError:
        pass
    try:
        Template.objects.create(name = name, path=path,
            subpages_columns=subpages_columns, images_columns=images_columns)
    except IntegrityError:
        pass

def get_default_template(obj_or_type):
    """Returns the default template for given object or type.

    **Parameters:**

    obj_or_type
        Must be an instance of BaseContent or a String with a valid type name.
    """
    ctr = get_info_for(obj_or_type)
    if ctr is None:
        return None
    else:
        return ctr.default_template

def get_templates(obj_or_type):
    """Returns allowed templates for passed object or type.

    **Parameters:**

    obj_or_type
        Must be an instance of BaseContent or a String with a valid type name.
    """
    ctr = get_info_for(obj_or_type)
    if ctr is None:
        return []
    else:
        return ctr.templates.all()
