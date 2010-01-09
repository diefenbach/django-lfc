# lfc imports
from lfc.models import ContentTypeRegistration
from lfc.models import Template
from lfc.models import BaseContent

# django imports
from django.contrib.contenttypes.models import ContentType

def get_info_for(obj_or_type):
    """Returns the content type registration for given object.
    """
    if isinstance(obj_or_type, BaseContent):
        type = obj_or_type.__class__.__name__.lower()
    else:
        type = obj_or_type

    try:
        return ContentTypeRegistration.objects.get(type = type)
    except ContentTypeRegistration.DoesNotExist:
        return None

def get_allowed_subtypes(obj=None):
    """Returns all allowed sub types for given object.
    """
    if obj is None:
        return ContentTypeRegistration.objects.filter(global_addable=True)

    ctr = get_info_for(obj)
    if ctr:
        return ctr.subtypes.all()
    else:
        return []

def register_sub_type_to(name, obj):
    """
    """
    try:
        base_ctr = ContentTypeRegistration.objects.get(name=name)
    except ContentTypeRegistration.DoesNotExist:
        pass

    try:
        sub_ctr = ContentTypeRegistration.objects.get(type =  obj.__name__.lower())
    except ContentTypeRegistration.DoesNotExist:
        pass

    base_ctr.subtypes.add(sub_ctr)

def register_content_type(obj, name, sub_types=[], templates=[], default_template=None):
    """Registers a content type. If a content type is already registered it
    updates it.
    """
    type = obj.__name__.lower()
    try:
        ctr, result = ContentTypeRegistration.objects.get_or_create(type=type, name=name)
        ctr.save()
    except:
        pass
    else:
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

def get_registered_content_types():
    """Returns all registered content types types as list of dicts.
    """
    conent_types = []
    for ct in ContentTypeRegistration.objects.all():
        conent_types.append({
            "type" : ct.type,
            "name" : ct.name,
        })

    return conent_types

def get_default_template_for(obj):
    """Returns the default template for given object.
    """
    try:
        ctr = ContentTypeRegistration.objects.get(type = obj.content_type)
    except ContentTypeRegistration.DoesNotExist:
        return None

    return ctr.default_template