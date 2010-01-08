# django imports
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import translation


# tagging imports
from tagging.forms import TagField

# lfc imports
from lfc.fields.autocomplete import AutoCompleteTagInput
from lfc.fields.autocomplete import ForeignKeySearchInput
from lfc.models import Page
from lfc.models import BaseContent
from lfc.models import Portal
from lfc.models import ContentTypeRegistration
from lfc.utils.registration import get_allowed_subtypes

class PageCommentsForm(forms.ModelForm):
    """
    """
    class Meta:
        model = Page
        fields = ("allow_comments", )

class PageTranslationForm(forms.ModelForm):
    """
    """
    class Meta:
        model = Page
        fields = ("title", "display_title", "slug", "text", "meta_keywords",
                  "meta_description", "tags")

class PageAddForm(forms.ModelForm):
    """
    """
    class Meta:
        model = Page
        fields = ("title", "slug", "text", "parent", "position")

    def __init__(self, *args, **kwargs):
        super(PageAddForm, self).__init__(*args, **kwargs)

        parents = Page.objects.exclude(special=True)
        parents = [(p.id, p.title) for p in parents]
        parents = sorted(parents, lambda a, b: cmp(a[1], b[1]))
        parents.insert(0, ("", "----------"))
        self.fields["parent"].choices = parents

class PageCoreDataForm(forms.ModelForm):
    """Core date form for pages.
    """
    tags = TagField(widget=AutoCompleteTagInput(), required=False)

    class Meta:
        model = Page
        fields = ("title", "display_title", "slug", "description", "text", "tags")

class PageSEOForm(forms.ModelForm):
    """
    """
    class Meta:
        model = Page
        fields = ( "meta_keywords", "meta_description")

class PageMetaDataForm(forms.ModelForm):
    """
    """
    def __init__(self, *args, **kwargs):
        super(PageMetaDataForm, self).__init__(*args, **kwargs)

        if hasattr(settings, "LFC_MULTILANGUAGE") and \
            settings.LFC_MULTILANGUAGE == False:
            del self.fields["canonical"]

        if hasattr(settings, "LFC_MULTILANGUAGE") and \
            settings.LFC_MULTILANGUAGE == False:
            del self.fields["language"]

        instance = kwargs.get("instance")

        # Display only parents within the current instance is allowed
        base_instance = instance.get_specific_type()
        ctr = ContentTypeRegistration.objects.get(type = base_instance.__class__.__name__.lower())

        if instance:
            language = instance.language

            # Display only for this instance registered templates
            obj = instance.get_specific_type()

            if len(ctr.templates.all()) < 2:
                del self.fields["template"]
            else:                
                self.fields["template"].choices = [(template.id, template.name) for template in ctr.templates.all()]
        else:
            language = translation.get_language()

        # Choices for canonical
        # Show only pages with the default language.
        if settings.LFC_MULTILANGUAGE:
            if instance.is_canonical():
                del self.fields["canonical"]
            else:
                canonicals = [(p.id, p.title) for p in BaseContent.objects.filter(language=settings.LANGUAGE_CODE)]
                canonicals.insert(0, ("", "----------"))
                self.fields["canonical"].choices = canonicals

        if instance:
            exclude = [p.id for p in instance.sub_objects.all()]
            exclude.append(instance.id)
        else:
            exclude = []

        # Display only neutral objects or objects in the same language
        parents = BaseContent.objects.exclude(pk__in=exclude)
        if not language == "0":
            parents = parents.filter(language__in=(language, "0"))

        parent_choices = []
        for parent in parents:
            if ctr in get_allowed_subtypes(parent.get_specific_type()):
                parent_choices.append((parent.id, parent.title))

        if len(parent_choices) < 0:
            del self.fields["parent"]
        else:    
            parent_choices = sorted(parent_choices, lambda a, b: cmp(a[1], b[1]))
            parent_choices.insert(0, ("", "----------"))
            self.fields["parent"].choices = parent_choices

        # Choices for standard objects. Display only children
        if instance:
            if not ctr.display_select_standard:
                del self.fields["standard"]
            else:
                children = instance.sub_objects.all()
                if len(children) == 0:
                    del self.fields["standard"]
                else:
                    if not language == "0":
                        children = instance.sub_objects.filter(language__in=(language, "0"))
                    else:
                        children = instance.sub_objects.all()

                    standards = [(p.id, p.title) for p in children]
                    standards = sorted(standards, lambda a, b: cmp(a[1], b[1]))
                    standards.insert(0, ("", "----------"))
                    self.fields["standard"].choices = standards
                    
        if instance:
            if not ctr.display_position:
                del self.fields["position"]

    class Meta:
        model = Page
        fields = ("template", "parent", "position", "standard", "active",
            "exclude_from_navigation", "exclude_from_search", "language",
            "canonical", "publication_date", )

class PortalCoreForm(forms.ModelForm):
    """Form for portal core data.
    """
    def __init__(self, *args, **kwargs):
        super(PortalCoreForm, self).__init__(*args, **kwargs)

        children = Page.objects.filter(parent=None).filter(special=False)
        standards = [(p.id, p.title) for p in children]
        standards = sorted(standards, lambda a, b: cmp(a[1], b[1]))
        standards.insert(0, ("", "----------"))
        self.fields["standard"].choices = standards

    class Meta:
        model = Portal

