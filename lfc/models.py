# python imports
import datetime
import re

# django imports
from django import template
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# tagging imports
from tagging import fields
from tagging.models import Tag 
from tagging.models import TaggedItem

# portlets imports
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking

# workflows imports
import workflows.utils
from workflows import WorkflowBase
from workflows.models import Workflow
from workflows.models import State
from workflows.models import StateObjectRelation

# permissions imports
from permissions import PermissionBase
from permissions.exceptions import Unauthorized
from permissions.models import Role
from permissions.models import ObjectPermission
from permissions.models import ObjectPermissionInheritanceBlock

# lfc imports
import lfc.utils
from lfc.fields.thumbs import ImageWithThumbsField
from lfc.managers import BaseContentManager
from lfc.settings import ALLOW_COMMENTS_CHOICES
from lfc.settings import ALLOW_COMMENTS_DEFAULT
from lfc.settings import ALLOW_COMMENTS_TRUE
from lfc.settings import LANGUAGE_CHOICES
from lfc.settings import ORDER_BY_CHOICES
from lfc.settings import IMAGE_SIZES
from lfc.settings import UPLOAD_FOLDER


class Application(models.Model):
    """Represents a LFC application.
    """
    name = models.CharField(max_length=100, unique=True)


class WorkflowStatesInformation(models.Model):
    """Stores some information about workflows

    **Attributes:**

    state
        The state for which information are stored.

    public
        True if the state is considered as public.

    review
        True if the state is considered as to be reviewed.
    """
    state = models.ForeignKey(State)
    public = models.BooleanField(default=False)
    review = models.BooleanField(default=False)

    def __unicode__(self):
        result = self.state.name
        if self.public:
            result += u" " + u"Public"

        if self.review:
            result += u" " + "Review"

        return result


class Template(models.Model):
    """A template displays the content of an object.

    **Attributes:**

    name
        The name of the template. This is displayed to the LFC user to select
        a template. Also used by developers to register a template to a content
        type.

    path
        The relative path to the template file according to Django templating
        engine.

    children_columns
        Stores the amount of columns for sub pages. This can be used for
        templates which displays the children of an object like overviews.

    images_columns
        Stores the amount of columens for images. This can be used for
        templates which displays the images of an object like galleries.

    """
    name = models.CharField(max_length=50, unique=True)
    path = models.CharField(max_length=100)
    children_columns = models.IntegerField(verbose_name=_(u"Subpages columns"), default=1)
    images_columns = models.IntegerField(verbose_name=_(u"Images columns"), default=1)

    class Meta:
        ordering = ("name", )

    def __unicode__(self):
        return self.name


class ContentTypeRegistration(models.Model):
    """Stores all registration relevant information of a registered content
    type.

    **Attributes:**

    type
        The type of the registered content type.

    name
        The name of the registered content type. This is displayed to the LFC
        users to add a new content type. Also used by developers for
        registration purposes.

    display_select_standard
        If set to true the user can select a standard page for the object.

    display_position
        If set to true the user can set the position of the intances.

    global_addable
        if set to true instances of the content type can be added to the
        portal.

    subtypes
        Allowed sub types which can be added to instances of the content type.

    templates
        Allowed templates which can be selected for instances of the content
        type.

    default_template
        The default template which is assigned when a instance of the content
        type is created.

    workflow
        Stores the workflow of this content type. All instances "inherit" this
        workflow and will get the initial state of it when created.
    """
    type = models.CharField(_(u"Type"), blank=True, max_length=100, unique=True)
    name = models.CharField(_(u"Name"), blank=True, max_length=100, unique=True)
    display_select_standard = models.BooleanField(_(u"Display select standard"), default=True)
    display_position = models.BooleanField(_(u"Display position"), default=True)

    global_addable = models.BooleanField(_(u"Global addable"), default=True)

    subtypes = models.ManyToManyField("self", verbose_name=_(u"Allowed sub types"), symmetrical=False, blank=True, null=True)
    templates = models.ManyToManyField("Template", verbose_name=_(u"Templates"), related_name="content_type_registrations")
    default_template = models.ForeignKey("Template", verbose_name=_(u"Default template"), blank=True, null=True)
    workflow = models.ForeignKey(Workflow, verbose_name=_(u"Workflow"), blank=True, null=True)

    class Meta:
        ordering = ("name", )

    def __unicode__(self):
        return self.name

    def get_subtypes(self):
        """Returns all allowed sub types for the belonging content type.
        """
        return self.subtypes.all()

    def get_templates(self):
        """Returns all allowed templates for the belonging content type.
        """
        return self.templates.all()


class Portal(models.Model, PermissionBase):
    """A portal is the root of all content objects. Stores global images and
    some general data about the site.

    **Attributes:**

    title:
        The title is displayed within the title tab of the site.

    standard:
        The object that is displayed if one browses to the root of the
        portal.

    from_email
        The e-mail address that is used as sender of outgoing mails.

    notification_emails
        These e-mail address get all notification mails. For instance all
        messages which are sent via the contact form to the portal.

    allow_comments
        Turns comments on/off generally.

    images
        The images which are associated with the portal. These images are
        considered global and can be used within any text editor field.

    files
        The files which are associated with the portal. These files are
        considered global and can be used within any text editor field.

    """
    title = models.CharField(_(u"Title"), blank=True, max_length=100)
    standard = models.ForeignKey("BaseContent", verbose_name=_(u"Standard"), blank=True, null=True, on_delete=models.SET_NULL)

    from_email = models.EmailField(_(u"From e-mail address"))
    notification_emails = models.TextField(_(u"Notification email addresses"))
    allow_comments = models.BooleanField(_(u"Allow comments"), default=False)

    images = generic.GenericRelation("Image", verbose_name=_(u"Images"),
        object_id_field="content_id", content_type_field="content_type")

    files = generic.GenericRelation("File", verbose_name=_(u"Files"),
        object_id_field="content_id", content_type_field="content_type")

    def __unicode__(self):
        return self.title

    @property
    def content_type(self):
        """
        Returns the content type of the portal in order to be consistent with
        BaseContent.
        """
        return u"portal"

    def get_content_type(self):
        """Readable / Displayable content type
        """
        return u"Portal"

    def get_absolute_url(self):
        """
        Returns the absolute url of the portal. It takes the current language
        into account.
        """
        language = translation.get_language()
        if language == settings.LANGUAGE_CODE:
            return reverse("lfc_base_view")
        else:
            return reverse("lfc_base_view", kwargs={"language": language})

    def get_notification_emails(self):
        """
        Returns the notification e-mail addresses as list.
        """
        adresses = re.split("[\s,]+", self.notification_emails)
        return adresses

    def are_comments_allowed(self):
        """
        Returns whether comments are allowed globally or not.
        """
        return self.allow_comments

    def get_parent_for_permissions(self):
        """
        Fullfills the contract of django-permissions. Returns just None as there
        is no parent for portlets.
        """
        return None

    def get_parent_for_portlets(self):
        """
        Fullfills the contract of django-portlets. Returns just None as there
        is no parent for portlets.
        """
        return None

    def get_template(self):
        """
        Returns the current template of the portal.
        """
        # TODO: Define default template in portal
        return Template.objects.get(name="Article")

    def get_children(self, request=None, *args, **kwargs):
        """
        Returns the children of the portal. If the request is passed the
        permissions of the current user is taken into account. Additionally
        other valid filters can be passed, e.g. slug = "page-1".
        """
        return lfc.utils.get_content_objects(request, parent=None, **kwargs)

    def has_permission(self, user, codename):
        """
        Overwrites django-permissions' has_permission in order to add LFC
        specific groups.
        """
        # Every user is also anonymous user
        try:
            roles = [lfc.utils.get_cached_object(Role, name="Anonymous").id]
        except Role.DoesNotExist:
            roles = []

        # Check whether the current user is the creator of the current object.
        try:
            if user == self.creator:
                roles.append(Role.objects.get(name="Owner").id)
        except (AttributeError, Role.DoesNotExist):
            pass

        return super(Portal, self).has_permission(user, codename, roles)

    def check_permission(self, user, codename):
        """
        Overwrites django-permissions' check_permission in order to add LFC
        specific groups.
        """
        if not self.has_permission(user, codename):
            raise Unauthorized("'%s' doesn't have permission '%s' for portal." % (user, codename))


class AbstractBaseContent(models.Model, WorkflowBase, PermissionBase):
    """The root of all content types. It provides the inheritable
    BaseContentManager.

    **Attributes:**

    objects
        The default content manager of LFC. Provides a restricted method which
        takes care of the current user's permissions.
    """
    objects = BaseContentManager()

    class Meta:
        abstract = True


class BaseContent(AbstractBaseContent):
    """Base content object. From this class all content types should inherit.
    It should never be instantiated.

    **Attributes:**

    content_type
        The content type of the specific content object.

    title
        The title of the object. By default this is displayed on top of every
        object.

    display_title
        Set to false to hide the title within the HTML of the object. This can
        be helpful to provide a custom title within the text field of an
        object.

    slug
        The part of URL within the parent object. By default the absolute URL
        of an object is created by all involved content objects.

    description:
        The description of an object. This is used within the overview
        template and search results.

    position:
        The ordinal number of the object within the parent object. This is
        used to order the child objects of an object.

    language
        The language of the object's content is in.

    canonical
        The base object of the object if the object is a translation another
        object.

    tags
        The tags of the object. Can be used to select certain objects or
        display a tag cloud.

    parent
        The parent object of an object. If set to None the object is a top
        object.

    template
        The current selected template of the object.

    standard
        The current selected standard object of the object. This can be
        selected out of the children of the object. If there is one, this is
        displayed instead of the object itself.

    order_by
        Defines how the children of the object are ordered (default is the
        position).

    exclude_from_navigation
        If set to True, the object is not displayed within the navigation (top
        tabs and navigation tree).

    exclude_from_search
        If set to True, the object is not displayed within search results.

    creator
        The user which has created this object.

    creation_date
        The date the object has been created.

    modification_date
        The date the object has been modified at last.

    publication_date
        The date the object has been published. TODO: implement this.

    start_date
        if given the object is only public when the start date is reached.

    end_date
        if given the object is only public when the end date is not reached
        yet.

    meta_title
        The meta title of the page. This is displayed within the title tag of
        the rendered HTML.

    meta_keywords
        The meta keywords of the object. This is displayed within the meta
        keywords tag of the rendered HTML.

    meta_description
        The meta description of the object. This is displayed within the meta
        description tag of the rendered HTML.

    images
        The images of the object.

    files
        The files of the object.

    allow_comments
        If set to true, the visitor of the object can leave a comment. If set
        to default the allow_comments state of the parent object is overtaken.

    searchable_text
        The content which is searched for this object. This attribute should
        not get directly. Rather the get_searchable_text method should be used.
    """
    content_type = models.CharField(_(u"Content type"), max_length=100, blank=True)

    title = models.CharField(_(u"Title"), max_length=100)
    display_title = models.BooleanField(_(u"Display title"), default=True)

    slug = models.SlugField(_(u"Slug"), max_length=100)

    description = models.TextField(_(u"Description"), blank=True)

    position = models.PositiveSmallIntegerField(_(u"Position"), default=1)

    language = models.CharField(_(u"Language"), max_length=10, choices=LANGUAGE_CHOICES, default="0")
    canonical = models.ForeignKey("self", verbose_name=_(u"Canonical"), related_name="translations", blank=True, null=True, on_delete=models.SET_NULL)

    tags = fields.TagField(_(u"Tags"))

    parent = models.ForeignKey("self", verbose_name=_(u"Parent"), blank=True, null=True, related_name="children")
    template = models.ForeignKey("Template", verbose_name=_(u"Template"), blank=True, null=True)
    standard = models.ForeignKey("self", verbose_name=_(u"Standard"), blank=True, null=True, on_delete=models.SET_NULL)
    order_by = models.CharField(_(u"Order by"), max_length=20, default="position", choices=ORDER_BY_CHOICES)

    exclude_from_navigation = models.BooleanField(_(u"Exclude from navigation"), default=False)
    exclude_from_search = models.BooleanField(_(u"Exclude from search results"), default=False)

    creator = models.ForeignKey(User, verbose_name=_(u"Creator"), null=True)
    creation_date = models.DateTimeField(_(u"Creation date"), auto_now_add=True)
    modification_date = models.DateTimeField(_(u"Modification date"), auto_now=True, auto_now_add=True)
    publication_date = models.DateTimeField(_(u"Publication date"), null=True, blank=True)
    start_date = models.DateTimeField(_(u"Start date"), null=True, blank=True)
    end_date = models.DateTimeField(_(u"End date"), null=True, blank=True)

    meta_title = models.CharField(_(u"Meta title"), max_length=100, default="<portal_title> - <title>")
    meta_keywords = models.TextField(_(u"Meta keywords"), blank=True, default="<tags>")
    meta_description = models.TextField(_(u"Meta description"), blank=True, default="<description>")

    images = generic.GenericRelation("Image", verbose_name=_(u"Images"),
        object_id_field="content_id", content_type_field="content_type")

    files = generic.GenericRelation("File", verbose_name=_(u"Files"),
        object_id_field="content_id", content_type_field="content_type")

    allow_comments = models.PositiveSmallIntegerField(_(u"Commentable"),
        choices=ALLOW_COMMENTS_CHOICES, default=ALLOW_COMMENTS_DEFAULT)

    searchable_text = models.TextField(blank=True)

    working_copy_base = models.ForeignKey("self", verbose_name=_(u"Working copy base"), related_name="working_copies", blank=True, null=True, on_delete=models.SET_NULL)

    version = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["position"]
        unique_together = ["parent", "slug", "language"]

    def __unicode__(self):
        return unicode(self.title)

    def has_meta_data_tab(self):
        return getattr(settings, "LFC_MANAGE_META_DATA", True)

    def has_children_tab(self):
        return getattr(settings, "LFC_MANAGE_CHILDREN", True)

    def has_images_tab(self):
        return getattr(settings, "LFC_MANAGE_IMAGES", True)

    def has_files_tab(self):
        return getattr(settings, "LFC_MANAGE_FILES", True)

    def has_portlets_tab(self):
        return getattr(settings, "LFC_MANAGE_PORTLETS", True)

    def has_comments_tab(self):
        return getattr(settings, "LFC_MANAGE_COMMENTS", True)

    def has_seo_tab(self):
        return getattr(settings, "LFC_MANAGE_SEO", True)

    def has_history_tab(self):
        return getattr(settings, "LFC_MANAGE_HISTORY", True)

    def has_permissions_tab(self):
        return getattr(settings, "LFC_MANAGE_PERMISSIONS", True)

    def get_tabs(self, request):
        return []

    def save(self, *args, **kwargs):
        """Django's default save method. This is overwritten to do some LFC
        related stuff when a content object is saved.
        """
        self.searchable_text = self.get_searchable_text()
        if self.content_type == "":
            self.content_type = self.__class__.__name__.lower()

        super(BaseContent, self).save(*args, **kwargs)

        # Set the initial state if there is none yet
        co = self.get_content_object()
        if workflows.utils.get_state(co) is None:
            workflows.utils.set_initial_state(co)

        lfc.utils.clear_cache()

    def delete(self, *args, **kwargs):
        """Djangos default delete method. This is overwritten to take care
        of generic relations that won't get deleted by django automatically.
        Note: if you delete objects via djangos bulk delete 
        (e.g. BaseContent.filter(foo=bar).delete()) this method will not get
        called. You have to delete this objects yourself.
        """
        ctype = ContentType.objects.get_for_model(self)

        # Delete tag-item-relations for object
        TaggedItem.objects.filter(object_id=self.id, content_type=ctype).delete()
        
        # Delete tags without any relations to items left
        Tag.objects.annotate(item_count=models.Count('items')).filter(item_count=0).delete()

        # Deletes images
        for image in self.images.all():
            try:
                image.image.delete()
            except AttributeError:
                pass
            try:
                image.delete()
            except AssertionError:
                pass

        # Delete files
        for myfile in self.files.all():
            try:
                myfile.file.delete()
            except AttributeError:
                pass
            try:
                myfile.delete()
            except AssertionError:
                pass

        # Delete workflows stuff
        StateObjectRelation.objects.filter(content_id=self.id, content_type=ctype).delete()

        # Delete permissions stuff
        ObjectPermission.objects.filter(content_id=self.id, content_type=ctype).delete()
        ObjectPermissionInheritanceBlock.objects.filter(content_id=self.id, content_type=ctype).delete()

        # Delete portlets stuff
        for pa in PortletAssignment.objects.filter(content_id=self.id, content_type=ctype):
            pa.portlet.delete()
            pa.delete()
        PortletBlocking.objects.filter(content_id=self.id, content_type=ctype).delete()
        
        # call Djangos delete method
        super(BaseContent, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        """Returns the absolute url of the instance. Takes care of nested
        content objects.
        """
        page = self.standard or self

        obj = page
        slugs = []
        while obj is not None:
            slugs.append(obj.slug)
            obj = obj.parent

        slugs.reverse()

        slug = "/".join(slugs)

        if page.language == settings.LANGUAGE_CODE:
            return ("lfc_base_view", (), {"slug": slug})
        elif page.language == "0":
            if page.parent:
                language = page.parent.language
                if language == "0":
                    return ("lfc_base_view", (), {"slug": slug})
            else:
                language = translation.get_language()

            if language == settings.LANGUAGE_CODE:
                return ("lfc_base_view", (), {"slug": slug})
            else:
                return ("lfc_base_view", (), {"slug": slug, "language": language})
        else:
            return ("lfc_base_view", (), {"slug": slug, "language": page.language})

    get_absolute_url = models.permalink(get_absolute_url)

    def add_history(self, request, action):
        """
        Adds a new history entry to the object.

        **Paramenters:**

        request
            The current request.

        action
            A string which describes what has been changed.
        """
        History.objects.create(obj=self.get_base_object(), action=action, user=request.user)

    def get_content_object(self):
        """Returns the specific content object of the instance. This method
        can be called if one has a BaseContent and want the specific content
        type.
        """
        # TODO: Ugly but works. There must be a cleaner way. isinstance doesn't
        # work of course.
        if self.__class__.__name__.lower() == "basecontent":
            return getattr(self, self.content_type)
        else:
            return self

    def get_base_object(self):
        """Returns the base content object of a specific content object.
        """
        if self.__class__.__name__.lower() == "basecontent":
            return self
        else:
            return self.basecontent_ptr

    def get_searchable_text(self):
        """Returns the searchable text of this content type. By default it
        takes the title the description of the instance into account. Sub
        classes can overwrite this method in order to add specific data.
        """
        result = self.title + " " + self.description
        return result.strip()

    def edit_form(self, **kwargs):
        """Returns the edit form for the object.
        """
        raise(NotImplementedError, "form has to be implemented by sub classed")

    def add_form(self, **kwargs):
        """Returns the add/edit form for the object.
        """
        from lfc.manage.forms import AddForm
        return AddForm(**kwargs)

    def get_ancestors(self):
        """Returns all ancestors of a content object.
        """
        ancestors = []
        obj = self
        while obj and obj.parent is not None:
            temp = obj.parent.get_content_object()
            ancestors.append(temp)
            obj = obj.parent

        return ancestors

    def get_ancestors_reverse(self):
        """Returns all ancestors of the page in reverse order.
        """
        ancestors = self.get_ancestors()
        ancestors.reverse()
        return ancestors

    def get_content_type(self):
        """Returns the content type of the object.
        """
        info = lfc.utils.registration.get_info(self.content_type)
        return info.name

    def get_descendants(self, request=None, result=None):
        """Returns all descendants of the content object. If the request is
        passed the permissions of the current user is taken into account.
        """
        if result is None:
            result = []
        for child in self.get_children(request):
            result.append(child)
            child.get_descendants(request, result)

        return result

    def has_children(self, request=None, *args, **kwargs):
        """Returns True if the object has children. If the request is
        passed the permissions of the current user is taken into account.
        Other valid filters can be passed also, e.g. slug = "page-1".
        """
        return len(lfc.utils.get_content_objects(request, parent=self, **kwargs)) > 0

    def get_children(self, request=None, *args, **kwargs):
        """Returns the children of the content object. If the request is
        passed the permissions of the current user is taken into account.
        Other valid filters can be passed also, e.g. slug = "page-1".
        """
        return lfc.utils.get_content_objects(request, parent=self, **kwargs)

    def get_image(self):
        """Returns the first image of a content object. If there is none it
        returns None.
        """
        images = self.images.all()
        try:
            return images[0]
        except IndexError:
            return None

    def get_meta_title(self):
        """Returns the meta title of the instance. Replaces some placeholders
        with the according content.
        """
        title = self.meta_title.replace("<title>", self.title)
        title = title.replace("<portal_title>", lfc.utils.get_portal().title)
        return title

    def get_meta_keywords(self):
        """Returns the meta keywords of the instance. Replaces some
        placeholders with the according content.
        """
        keywords = self.meta_keywords.replace("<title>", self.title)
        keywords = keywords.replace("<description>", self.description)
        keywords = keywords.replace("<tags>", self.tags)
        return keywords

    def get_meta_description(self):
        """Returns the meta description of the instance. Replaces some
        placeholders with the according content.
        """
        description = self.meta_description.replace("<title>", self.title)
        description = description.replace("<description>", self.description)
        description = description.replace("<tags>", self.tags)
        return description

    def get_template(self):
        """Returns the current selected template of the object.
        """
        if self.template is not None:
            return self.template
        else:
            default_template = lfc.utils.registration.get_default_template(self)
            if default_template is not None:
                return default_template
            else:
                return lfc.utils.get_portal().get_template()

    def get_title(self):
        """Returns the title of the object. Takes display_title into account.
        """
        return self.display_title and self.title or ""

    def is_canonical(self):
        """Returns true if the language of the page is the default language.
        """
        return self.language in (settings.LANGUAGE_CODE, "0")

    def get_canonical(self, request):
        """Returns the canonical object of this instance. If the instance is
        the canonical object it returns itself. Takes care of the current
        user's permission (therefore it needs the request).
        """
        if self.is_canonical():
            return self
        else:
            if self.canonical:
                obj = BaseContent.objects.get(pk=self.canonical.id)
                if self.has_permission(request.user, "view"):
                    return obj.get_content_object()
                else:
                    return None

    def is_translation(self):
        """Returns true if the instance is a translation of another instance.
        """
        return not self.is_canonical()

    def has_language(self, request, language):
        """Returns true if there is a translation of the instance in the
        requested language. It returns also true if the instance itself is
        within the requested language or if there is a connected instance with
        neutral language.
        """
        if self.language == "0":
            return True

        if self.language == language:
            return True

        if self.is_translation():
            canonical = self.get_canonical(request)
            if canonical and canonical.language == language:
                return True
            if canonical and canonical.get_translation(request, language):
                return True

        if self.is_canonical():
            if self.get_translation(request, language):
                return True

        return False

    def get_translation(self, request, language):
        """Returns connected translation for requested language. Returns None
        if the requested language doesn't exist.
        """
        # TODO: Should there a instance be returned even if the instance is a
        # translation?
        if self.is_translation():
            return None
        try:
            translation = self.translations.get(language=language).get_content_object()
            if translation.has_permission(request.user, "view"):
                return translation
            else:
                return None

        except BaseContent.DoesNotExist:
            return None

    def are_comments_allowed(self):
        """Returns true if comments for this instance are allowed. Takes also
        the setup of parent objects into account (if the instance' comments
        setup is set to "default").
        """
        if self.allow_comments == ALLOW_COMMENTS_DEFAULT:
            if self.parent:
                return self.parent.are_comments_allowed()
            else:
                return lfc.utils.get_portal().are_comments_allowed()
        else:
            if self.allow_comments == ALLOW_COMMENTS_TRUE:
                return True
            else:
                return False

    def get_parent_for_portlets(self):
        """Returns the parent from which portlets should be inherited portlets.
        The implementation of this method is a requirement from django-portlets.
        """
        return self.parent and self.parent.get_content_object() or lfc.utils.get_portal()

    def set_context(self, request):
        self.context = self.get_context(request)

    def get_context(self, request):
        """Calculates and returns the request context.
        """
        obj_template = self.get_template()

        # Children
        # CACHE
        children_cache_key = "%s-children-%s-%s-%s" % \
            (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.content_type, self.id, request.user.id)
        sub_objects = cache.get(children_cache_key)
        if sub_objects is None:
            # Get sub objects (as LOL if requested)
            if obj_template.children_columns == 0:
                sub_objects = self.get_children(request)
            else:
                sub_objects = lfc.utils.getLOL(self.get_children(request), obj_template.children_columns)

            cache.set(children_cache_key, sub_objects)

        # Images
        # CACHE
        images_cache_key = "%s-images-%s-%s" % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.content_type, self.id)
        cached_images = cache.get(images_cache_key)
        if cached_images:
            image = cached_images["image"]
            images = cached_images["images"]
            subimages = cached_images["subimages"]
        else:
            temp_images = list(self.images.all())
            if temp_images:
                if obj_template.images_columns == 0:
                    images = temp_images
                    image = images[0]
                    subimages = temp_images[1:]
                else:
                    images = lfc.utils.getLOL(temp_images, obj_template.images_columns)
                    subimages = lfc.utils.getLOL(temp_images[1:], obj_template.images_columns)
                    image = images[0][0]
            else:
                image = None
                images = []
                subimages = []

            cache.set(images_cache_key, {
                "image": image,
                "images": images,
                "subimages": subimages
            })

        self.context = RequestContext(request, {
            "lfc_context": self,
            "self": self,
            "images": images,
            "image": image,
            "subimages": subimages,
            "files": self.files.all(),
            "sub_objects": sub_objects,
            "portal": lfc.utils.get_portal(),
        })

        return self.context

    def render(self, request):
        """Renders the object content.
        """
        if self.context is None:
            self.context = self.get_context()

        # CACHE
        template_cache_key = "%s-template-%s-%s" % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.content_type, self.id)
        obj_template = cache.get(template_cache_key)
        if obj_template is None:
            obj_template = self.get_template()
            cache.set(template_cache_key, obj_template)

        tags = ""
        for tag in getattr(settings, "LFC_TAGS", []):
            tags += "{%% load %s %%}" % tag

        # Render twice. This makes tags within text / short_text possible.
        result = render_to_string(obj_template.path, self.context)
        result = template.Template(tags + " " + result).render(self.context)
        return result

    # django-permissions
    def get_parent_for_permissions(self):
        """Returns the parent from which permissions are inherited. The
        implementation of this method is a requirement from django-permissions.
        """
        return self.parent and self.parent.get_content_object() or lfc.utils.get_portal()

    def has_permission(self, user, codename):
        """Overwrites django-permissions' has_permission in order to add LFC
        specific groups.
        """
        try:
            return user.permissions[str(self.id)][codename]
        except:
            pass

        # Every user is also anonymous user
        try:
            roles = [Role.objects.get(name="Anonymous")]
        except Role.DoesNotExist:
            roles = []

        # Check whether the current user is the creator of the current object.
        try:
            if user == self.creator:
                roles.append(Role.objects.get(name="Owner"))
        except (AttributeError, Role.DoesNotExist):
            pass

        result = super(BaseContent, self).has_permission(user, codename, roles)

        if not getattr(user, "permissions", False):
            user.permissions = {}

        if not user.permissions.get(str(self.id), False):
            user.permissions[str(self.id)] = {}

        user.permissions[str(self.id)][codename] = result

        return result

    def check_permission(self, user, codename):
        """Overwrites django-permissions' check_permission in order to add LFC
        specific groups.
        """
        if not self.has_permission(user, codename):
            raise Unauthorized("'%s' doesn't have permission '%s' for object '/%s' (%s)." % (user, codename, self.slug, self.__class__.__name__))

    def is_active(self, user):
        """Returns True if now is between start and end date of the object.
        """
        if user.is_superuser:
            return True

        if self.start_date or self.end_date:
            started = True
            ended = False

            now = datetime.datetime.now()
            if self.start_date and self.start_date > now:
                started = False
            if self.end_date and now >= self.end_date:
                ended = True

            return started and not ended
        else:
            return True

    def reindex(self):
        """Reindexes the objects's searchable text.
        """
        self.searchable_text = self.get_searchable_text()
        self.save()

    def is_working_copy(self):
        """
        Returns True if the object is a working copy.
        """
        try:
            return bool(self.working_copy_base)
        except BaseContent.DoesNotExist:
            return False

    def has_working_copy(self):
        """
        Returns True if the object has a working copy.
        """
        return self.working_copies.count() > 0

    def get_working_copy(self):
        """
        Returns the working copy of the object. If there is none, it returns
        None.
        """
        try:
            return self.working_copies.all()[0]
        except IndexError:
            return None

    # django-workflows
    def get_allowed_transitions(self, user):
        """Returns all allowed permissions for the passed user.
        """
        state = self.get_state()
        if state is None:
            return []

        transitions = []
        for transition in state.transitions.all():
            permission = transition.permission
            if permission is None or self.has_permission(user, permission.codename):
                transitions.append(transition)

        return transitions


class Image(models.Model):
    """An image which can be displayes within HTML. Generates automatically
    various sizes.

    title
        The title of the image. Used within the title and alt tag of the
        image.

    slug
        The URL of the image

    content
        The content object the image belongs to (optional)

    position
        The ord number within the content object

    caption
        The caption of the image. Can be used within the content (optional)

    description
        A description of the image. Can be used within the content
        (optional)

    image
        The image file.
    """
    title = models.CharField(_(u"Title"), blank=True, max_length=100)
    slug = models.SlugField(_(u"Slug"), max_length=100)

    content_type = models.ForeignKey(ContentType, verbose_name=_(u"Content type"), related_name="images", blank=True, null=True)
    content_id = models.PositiveIntegerField(_(u"Content id"), blank=True, null=True)
    content = generic.GenericForeignKey(ct_field="content_type", fk_field="content_id")

    position = models.SmallIntegerField(_(u"Position"), default=999)
    caption = models.CharField(_(u"Caption"), blank=True, max_length=100)
    description = models.TextField(_(u"Description"), blank=True)
    creation_date = models.DateTimeField(_(u"Creation date"), auto_now_add=True)
    image = ImageWithThumbsField(_(u"Image"), upload_to=UPLOAD_FOLDER, sizes=IMAGE_SIZES)

    class Meta:
        ordering = ("position", )

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return ("gallery.views.photo", (), {"slug": self.slug})
    get_absolute_url = models.permalink(get_absolute_url)


class File(models.Model):
    """A downloadable file.

    **Attributes:**

    title
        The title of the file.

    slug
        The URL of the file.

    content
        The content object the file belongs to (optional).

    position
        The ordinal number within the content object. Used to order the files.

    description
        A long description of the file. Can be used within the content
        (optional).

    file
        The binary file.
    """
    title = models.CharField(blank=True, max_length=100)
    slug = models.SlugField(max_length=100)

    content_type = models.ForeignKey(ContentType, verbose_name=_(u"Content type"), related_name="files", blank=True, null=True)
    content_id = models.PositiveIntegerField(_(u"Content id"), blank=True, null=True)
    content = generic.GenericForeignKey(ct_field="content_type", fk_field="content_id")

    position = models.SmallIntegerField(default=999)
    description = models.TextField(blank=True)
    creation_date = models.DateTimeField(_(u"Creation date"), auto_now_add=True)
    file = models.FileField(upload_to="files")

    class Meta:
        ordering = ("position", )

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("lfc_file", kwargs={"id": self.id})


class History(models.Model):
    """
    Stores some history about a content object.
    """
    obj = models.ForeignKey(BaseContent, verbose_name=_(u"Content object"), related_name="content_objects")
    action = models.CharField(_(u"Action"), max_length=100)
    user = models.ForeignKey(User, verbose_name=_(u"User"), related_name="user")
    creation_date = models.DateTimeField(_(u"Creation date"), auto_now_add=True)

    class Meta:
        ordering = ("-creation_date", )
