# django imports
from django import forms
from django.forms.util import ErrorList
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

# tagging imports
from tagging.forms import TagField

# permissions imports
from permissions.models import Role
from permissions.models import PrincipalRoleRelation

# lfc imports
from lfc.fields.autocomplete import AutoCompleteTagInput
from lfc.models import Page
from lfc.models import BaseContent
from lfc.models import Portal
from lfc.models import ContentTypeRegistration
from lfc.utils.registration import get_allowed_subtypes
from lfc.utils.registration import get_info

class RoleForm(forms.ModelForm):
    """
    """
    class Meta:
        model = Role

class GroupForm(forms.ModelForm):
    """
    """
    class Meta:
        model = Group
        exclude = ("permissions", )

class UserForm(forms.ModelForm):
    """
    """
    roles = forms.MultipleChoiceField(label=_("Roles"), required=False)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        roles = Role.objects.exclude(name__in=("Anonymous", "Owner"))
        self.fields["roles"].choices = [(r.id, r.name) for r in roles]

        self.initial.update({
            "roles" : [prr.role.id for prr in PrincipalRoleRelation.objects.filter(user=self.instance)]})

    def save(self, commit=True):
        """
        """
        role_ids = self.data.get("roles", [])

        for role in Role.objects.all():

            if str(role.id) in role_ids:
                try:
                    prr = PrincipalRoleRelation.objects.get(user=self.instance, role=role)
                except PrincipalRoleRelation.DoesNotExist:
                    PrincipalRoleRelation.objects.create(user=self.instance, role=role)
            else:
                try:
                    prr = PrincipalRoleRelation.objects.get(user=self.instance, role=role)
                except PrincipalRoleRelation.DoesNotExist:
                    pass
                else:
                    prr.delete()

        del self.fields["roles"]
        super(UserForm, self).save(commit)

    class Meta:
        model = User
        exclude = ("user_permissions", "password", "last_login", "date_joined")

class UserAddForm(forms.ModelForm):
    """
    """
    roles = forms.MultipleChoiceField(label=_("Roles"), required=False)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password (again)"), widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)

        roles = Role.objects.exclude(name__in=("Anonymous", "Owner"))
        self.fields["roles"].choices = [(r.id, r.name) for r in roles]

    def save(self, commit=True):
        """
        """        
        del self.fields["roles"]
        return super(UserAddForm, self).save(commit)

    def clean(self):
        """
        """
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")

        if p1 != p2:
            self._errors["password1"] = ErrorList(["Passwords must be equal"])
            self._errors["password2"] = ErrorList(["Passwords  must be equal"])

        return self.cleaned_data

    class Meta:
        model = User
        exclude = ("user_permissions", "password", "last_login", "date_joined")

class ContentTypeRegistrationForm(forms.ModelForm):
    """
    """
    class Meta:
        model = ContentTypeRegistration
        exclude = ("type", "name")

class CommentsForm(forms.ModelForm):
    """
    """
    class Meta:
        model = Page
        fields = ("allow_comments", )

class CoreDataForm(forms.ModelForm):
    """Core date form for pages.
    """
    tags = TagField(widget=AutoCompleteTagInput(), required=False)

    class Meta:
        model = Page
        fields = ("title", "display_title", "slug", "description", "text", "tags")

class SEOForm(forms.ModelForm):
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

        instance = kwargs.get("instance").get_content_object()
        language = instance.language
        ctr = get_info(instance)

        if not getattr(settings, "LFC_MULTILANGUAGE"):
            del self.fields["canonical"]
            del self.fields["language"]

        # Templates - display only registered templates for this instance
        if len(ctr.templates.all()) < 2:
            del self.fields["template"]
        else:
            self.fields["template"].choices = [(template.id, _(template.name)) for template in ctr.templates.all()]

        # Canonical - display only pages with default language
        if settings.LFC_MULTILANGUAGE:
            if instance.is_canonical():
                del self.fields["canonical"]
            else:
                canonicals = [(p.id, p.title) for p in BaseContent.objects.filter(language=settings.LANGUAGE_CODE)]
                canonicals.insert(0, ("", "----------"))
                self.fields["canonical"].choices = canonicals

        # Parents - display only objects in the same or neutral language
        # exclude = [p.id for p in instance.children.all()]
        # exclude.append(instance.id)
        #
        # parents = BaseContent.objects.exclude(pk__in=exclude)
        # if not language == "0":
        #     parents = parents.filter(language__in=(language, "0"))
        #
        # parent_choices = []
        # for parent in parents:
        #     if ctr in get_allowed_subtypes(parent.get_content_object()):
        #         parent_choices.append((parent.id, parent.title))
        #
        # if len(parent_choices) < 1:
        #     del self.fields["parent"]
        # else:
        #     parent_choices = sorted(parent_choices, lambda a, b: cmp(a[1], b[1]))
        #     parent_choices.insert(0, ("", "----------"))
        #     self.fields["parent"].choices = parent_choices

        # Standard - display only children of the current instance
        if not ctr.display_select_standard:
            del self.fields["standard"]
        else:
            children = instance.children.all()
            if len(children) == 0:
                del self.fields["standard"]
            else:
                if not language == "0":
                    children = instance.children.filter(language__in=(language, "0"))
                else:
                    children = instance.children.all()

                standards = [(p.id, p.title) for p in children]
                standards = sorted(standards, lambda a, b: cmp(a[1], b[1]))
                standards.insert(0, ("", "----------"))
                self.fields["standard"].choices = standards

        # Position
        if not ctr.display_position:
            del self.fields["position"]

    class Meta:
        model = Page
        fields = ("template", "standard", "exclude_from_navigation",
            "exclude_from_search", "language", "canonical", "publication_date", )

class PortalCoreForm(forms.ModelForm):
    """Form for portal core data.
    """
    def __init__(self, *args, **kwargs):
        super(PortalCoreForm, self).__init__(*args, **kwargs)

        children = BaseContent.objects.filter(parent=None)
        standards = [(p.id, p.title) for p in children]
        standards = sorted(standards, lambda a, b: cmp(a[1], b[1]))
        standards.insert(0, ("", "----------"))
        self.fields["standard"].choices = standards

    class Meta:
        model = Portal
