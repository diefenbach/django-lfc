# django imports
from django import forms
from django.conf import settings
from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.comments.models import Comment
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _

# permissions imports
from permissions.models import Permission
from permissions.models import PrincipalRoleRelation
from permissions.models import Role

# workflows imports
from workflows.models import Workflow
from workflows.models import State
from workflows.models import Transition

# lfc imports
from lfc.fields.readonly import ReadOnlyInput
from lfc.fields.wysiwyg import WYSIWYGInput
from lfc.models import BaseContent
from lfc.models import ContentTypeRegistration
from lfc.models import File
from lfc.models import Image
from lfc.models import Portal
from lfc.models import Template
from lfc.utils.registration import get_info


class AddForm(forms.Form):
    """The default add form for content objects.
    """
    title = forms.CharField()
    slug = forms.CharField()
    description = forms.CharField(required=False, widget=forms.Textarea)


class ImageForm(forms.ModelForm):
    """Form to edit an Image.
    """
    class Meta:
        model = Image
        exclude = ("image", "content_type", "content_id", "slug", "position")

    def __init__(self, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)
        self.fields["description"].widget = WYSIWYGInput()


class FileForm(forms.ModelForm):
    """Form to edit a File.
    """
    class Meta:
        model = File
        exclude = ("file", "content_type", "content_id", "slug", "position")

    def __init__(self, *args, **kwargs):
        super(FileForm, self).__init__(*args, **kwargs)
        self.fields["description"].widget = WYSIWYGInput()


class WorkflowAddForm(forms.ModelForm):
    """Form to add a workflow.
    """
    class Meta:
        model = Workflow
        exclude = ("permissions", "initial_state")


class WorkflowForm(forms.ModelForm):
    """Form to add/edit a workflow.
    """
    def __init__(self, *args, **kwargs):
        super(WorkflowForm, self).__init__(*args, **kwargs)

        instance = kwargs.get("instance")
        if instance:
            self.fields["initial_state"].choices = [(s.id, _(s.name)) for s in instance.states.all()]

    class Meta:
        model = Workflow
        exclude = ("permissions", )


class StateForm(forms.ModelForm):
    """Form to edit a workflow state.
    """
    def __init__(self, *args, **kwargs):
        super(StateForm, self).__init__(*args, **kwargs)

        instance = kwargs.get("instance")
        if instance:
            self.fields["transitions"].choices = [(t.id, _(t.name)) for t in Transition.objects.filter(workflow=instance.workflow)]

    class Meta:
        model = State
        exclude = ["workflow"]


class TransitionForm(forms.ModelForm):
    """Form to edit a workflow transition.
    """
    def __init__(self, *args, **kwargs):
        super(TransitionForm, self).__init__(*args, **kwargs)

        instance = kwargs.get("instance")
        if instance:
            states = [("", "---------")]
            states.extend([(s.id, _(s.name)) for s in State.objects.filter(workflow=instance.workflow)])
            self.fields["destination"].choices = states

            permissions = [("", "---------")]
            permissions.extend([(p.id, _(p.name)) for p in Permission.objects.all()])
            self.fields["permission"].choices = permissions

    class Meta:
        model = Transition
        exclude = ["workflow"]


class RoleForm(forms.ModelForm):
    """Form to add/edit a Role.
    """
    groups = forms.MultipleChoiceField(label=_("Groups"), required=False)

    class Meta:
        model = Role

    def __init__(self, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        self.fields["groups"].choices = [(g.id, g.name) for g in Group.objects.all()]
        self.initial.update({
            "groups": [prr.group.id for prr in PrincipalRoleRelation.objects.filter(role=self.instance).exclude(group=None)]
        })

    def save(self, commit=True):
        group_ids = self.data.getlist("groups")
        for group in Group.objects.all():
            if str(group.id) in group_ids:
                try:
                    prr = PrincipalRoleRelation.objects.get(group=group, role=self.instance, content_id=None)
                except PrincipalRoleRelation.DoesNotExist:
                    PrincipalRoleRelation.objects.create(group=group, role=self.instance)
            else:
                try:
                    prr = PrincipalRoleRelation.objects.get(group=group, role=self.instance, content_id=None)
                except PrincipalRoleRelation.DoesNotExist:
                    pass
                else:
                    prr.delete()

        del self.fields["groups"]
        return super(RoleForm, self).save(commit)


class GroupForm(forms.ModelForm):
    """Form to add/edit a Group.
    """
    roles = forms.MultipleChoiceField(label=_("Roles"), required=False)

    class Meta:
        model = Group
        exclude = ("permissions", )

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)

        roles = Role.objects.exclude(name__in=("Anonymous", "Owner"))
        self.fields["roles"].choices = [(r.id, _(r.name)) for r in roles]

        self.initial.update({
            "roles": [prr.role.id for prr in PrincipalRoleRelation.objects.filter(group=self.instance, content_id=None)]
        })

    def save(self, commit=True):
        role_ids = self.data.getlist("roles")

        for role in Role.objects.all():

            if str(role.id) in role_ids:
                try:
                    prr = PrincipalRoleRelation.objects.get(group=self.instance, role=role, content_id=None)
                except PrincipalRoleRelation.DoesNotExist:
                    PrincipalRoleRelation.objects.create(group=self.instance, role=role)
            else:
                try:
                    prr = PrincipalRoleRelation.objects.get(group=self.instance, role=role, content_id=None)
                except PrincipalRoleRelation.DoesNotExist:
                    pass
                else:
                    prr.delete()

        del self.fields["roles"]
        return super(GroupForm, self).save(commit)


class UserForm(forms.ModelForm):
    """Form to add/edit an User.
    """
    roles = forms.MultipleChoiceField(label=_("Roles"), required=False)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        roles = Role.objects.exclude(name__in=("Anonymous", "Owner"))
        self.fields["roles"].choices = [(r.id, _(r.name)) for r in roles]

        self.initial.update({
            "roles": [prr.role.id for prr in PrincipalRoleRelation.objects.filter(user=self.instance)]})

    def save(self, commit=True):
        role_ids = self.data.getlist("roles")
        for role in Role.objects.all():

            if str(role.id) in role_ids:
                try:
                    prr = PrincipalRoleRelation.objects.get(user=self.instance, role=role, content_id=None)
                except PrincipalRoleRelation.DoesNotExist:
                    PrincipalRoleRelation.objects.create(user=self.instance, role=role, content_id=None)
            else:
                try:
                    prr = PrincipalRoleRelation.objects.get(user=self.instance, role=role, content_id=None)
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
    """Form to display content type registration.
    """
    def __init__(self, *args, **kwargs):
        super(ContentTypeRegistrationForm, self).__init__(*args, **kwargs)
        templates = [(s.id, _(s.name)) for s in Template.objects.all()]
        self.fields["templates"].choices = templates
        self.fields["default_template"].choices = templates
        self.fields["subtypes"].choices = [(s.id, _(s.name)) for s in ContentTypeRegistration.objects.all()]
        self.fields["workflow"].choices = [(s.id, _(s.name)) for s in Workflow.objects.all()]

    class Meta:
        model = ContentTypeRegistration
        exclude = ("type", "name")


class CommentForm(forms.ModelForm):
    """Form to edit a comment.
    """
    class Meta:
        model = Comment
        exclude = ("content_type", "object_pk", "site")


class CommentsForm(forms.ModelForm):
    """Form to update/delete comments.
    """
    class Meta:
        model = BaseContent
        fields = ("allow_comments", )


class SEOForm(forms.ModelForm):
    """SEO form for objects.
    """
    class Meta:
        model = BaseContent
        fields = ("meta_title", "meta_keywords", "meta_description")


class MetaDataForm(forms.ModelForm):
    """Form to display object metadata form.
    """
    def __init__(self, request, *args, **kwargs):
        super(MetaDataForm, self).__init__(*args, **kwargs)

        self.fields["publication_date"].widget = widgets.AdminSplitDateTime()
        self.fields["start_date"].widget = widgets.AdminSplitDateTime()
        self.fields["end_date"].widget = widgets.AdminSplitDateTime(attrs={"required": False})

        instance = kwargs.get("instance").get_content_object()

        if not instance.has_permission(request.user, "manage_content"):
            self.fields["creator"].widget = ReadOnlyInput()

        language = instance.language
        ctr = get_info(instance)

        if not getattr(settings, "LFC_MULTILANGUAGE"):
            del self.fields["canonical"]
            del self.fields["language"]

        # Template
        self.fields["template"].choices = [(template.id, _(template.name)) for template in ctr.templates.all()]

        # Canonical - display only pages with default language
        if settings.LFC_MULTILANGUAGE:
            if instance.is_canonical():
                del self.fields["canonical"]
            else:
                canonicals = [(p.id, p.title) for p in BaseContent.objects.filter(language=settings.LANGUAGE_CODE)]
                canonicals.insert(0, ("", "----------"))
                self.fields["canonical"].choices = canonicals

        # Standard - display only children of the current instance
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
        model = BaseContent
        fields = ("template", "standard", "order_by", "language", "canonical",
            "exclude_from_navigation", "exclude_from_search", "creator",
            "publication_date", "start_date", "end_date")


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
