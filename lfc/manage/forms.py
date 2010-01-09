# django imports
from django import forms
from django.conf import settings

# tagging imports
from tagging.forms import TagField

# lfc imports
from lfc.fields.autocomplete import AutoCompleteTagInput
from lfc.models import Page
from lfc.models import BaseContent
from lfc.models import Portal
from lfc.utils.registration import get_allowed_subtypes
from lfc.utils.registration import get_info_for

class CommentsForm(forms.ModelForm):
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

class MetaDataForm(forms.ModelForm):
    """
    """
    def __init__(self, *args, **kwargs):
        super(MetaDataForm, self).__init__(*args, **kwargs)

        instance = kwargs.get("instance").get_specific_type()
        language = instance.language
        ctr = get_info_for(instance)

        if not getattr(settings, "LFC_MULTILANGUAGE"):
            del self.fields["canonical"]
            del self.fields["language"]

        # Templates - display only registered templates for this instance
        if len(ctr.templates.all()) < 2:
            del self.fields["template"]
        else:
            self.fields["template"].choices = [(template.id, template.name) for template in ctr.templates.all()]

        # Canonical - display only pages with default language
        if settings.LFC_MULTILANGUAGE:
            if instance.is_canonical():
                del self.fields["canonical"]
            else:
                canonicals = [(p.id, p.title) for p in BaseContent.objects.filter(language=settings.LANGUAGE_CODE)]
                canonicals.insert(0, ("", "----------"))
                self.fields["canonical"].choices = canonicals

        # Parents - display only objects in the same or neutral language
        exclude = [p.id for p in instance.sub_objects.all()]
        exclude.append(instance.id)

        parents = BaseContent.objects.exclude(pk__in=exclude)
        if not language == "0":
            parents = parents.filter(language__in=(language, "0"))

        parent_choices = []
        for parent in parents:
            if ctr in get_allowed_subtypes(parent.get_specific_type()):
                parent_choices.append((parent.id, parent.title))

        if len(parent_choices) < 1:
            del self.fields["parent"]
        else:
            parent_choices = sorted(parent_choices, lambda a, b: cmp(a[1], b[1]))
            parent_choices.insert(0, ("", "----------"))
            self.fields["parent"].choices = parent_choices

        # Standard - display only children of the current instance
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

        # Position
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

