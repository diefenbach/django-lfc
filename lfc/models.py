# python imports
import datetime
import re
import random

# django imports
import portlets
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_syncdb
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

# tagging imports
import tagging.utils
import tagging.models
from tagging import fields

# portlets imports
import portlets
from portlets.models import Portlet
from portlets.utils import register_portlet

# lfc imports
import lfc.utils
import lfc.settings
from lfc.fields.thumbs import ImageWithThumbsField
from lfc.settings import ALLOW_COMMENTS_CHOICES
from lfc.settings import ALLOW_COMMENTS_DEFAULT
from lfc.settings import ALLOW_COMMENTS_TRUE
from lfc.settings import LANGUAGE_CHOICES


class Template(models.Model):
    """A template displays the content of an object.
    """
    name = models.CharField(max_length=50)
    file_name = models.CharField(max_length=100)
    subpages_columns = models.IntegerField(verbose_name=_(u"Subpages columns"), default=1)
    images_columns = models.IntegerField(verbose_name=_(u"Images columns"), default=1)

    class Meta:
        ordering = ("name", )

    def __unicode__(self):
        return self.name

class ContentTypeRegistration(models.Model):
    """
    """
    type = models.CharField(blank=True, max_length=100, unique=True)
    name = models.CharField(blank=True, max_length=100, unique=True)
    display_select_standard = models.BooleanField(default=True)
    display_position = models.BooleanField(default=True)
    global_addable = models.BooleanField(default=True)

    subtypes = models.ManyToManyField("self", symmetrical=False, blank=True, null=True)
    templates = models.ManyToManyField("Template", related_name="content_type_registrations")
    default_template = models.ForeignKey("Template", blank=True, null=True)


    class Meta:
        ordering = ("name", )

    def __unicode__(self):
        return self.name

class Portal(models.Model):
    """A portal has content objects.
    """

    title = models.CharField(_(u"Title"), blank=True, max_length=100)
    standard = models.ForeignKey("BaseContent", verbose_name = _(u"Page"), blank=True, null=True)

    from_email = models.EmailField(_(u"From e-mail address"))
    notification_emails  = models.TextField(_(u"Notification email addresses"))
    allow_comments = models.BooleanField(_(u"Allow comments"), default=False)

    tags = fields.TagField(_(u"Tags"))

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        language = translation.get_language()
        if language == settings.LANGUAGE_CODE:
            return reverse("lfc_portal")
        else:
            return reverse("lfc_portal", kwargs={"language" : language})

    def get_notification_emails(self):
        """Returns the notification e-mail addresses as list.
        """
        adresses = re.split("[\s,]+", self.notification_emails)
        return adresses

    def are_comments_allowed(self):
        """Returns whether comments are allowed globally or not.
        """
        return self.allow_comments

    def get_parent_for_portlets(self):
        return None

    # TODO: Define default template in portal
    def get_template(self):
        """Returns the template of the portal
        """
        return Template.objects.get(name="Article")

class BaseContent(models.Model):
    """Base content object. From this model all content types should inherit.
    """
    class Meta:
        ordering = ["position"]
        unique_together = ["parent", "slug", "language"]

    def __unicode__(self):
        return unicode(self.title)

    def get_specific_type(self):
        """
        """
        # TODO: Ugly but works. There must be a cleaner way. isinstance doesn't
        # work of course.
        if self.__class__.__name__.lower() == "basecontent":
            return getattr(self, self.content_type)
        else:
            return self

    content_type = models.CharField(_(u"Content type"), max_length=100, blank=True)

    title = models.CharField(_(u"Title"), max_length=100)
    display_title = models.BooleanField(default=True)

    slug = models.SlugField(_(u"Slug"))

    description = models.TextField(_(u"Short text"), blank=True)

    position = models.PositiveSmallIntegerField(_(u"Position"), default=1)

    language = models.CharField(_(u"Language"), max_length=10, choices=LANGUAGE_CHOICES, default="0")
    canonical = models.ForeignKey("self", verbose_name=_(u"Canonical"), related_name="translations", blank=True, null=True)

    tags = fields.TagField(_(u"Tags"))

    parent = models.ForeignKey("self", verbose_name=_(u"Parent"), blank=True, null=True, related_name="sub_objects")
    template = models.ForeignKey("Template", verbose_name=_(u"Template"), blank=True, null=True)
    standard = models.ForeignKey("self", verbose_name=_(u"Standard"), blank=True, null=True)

    active = models.BooleanField(_(u"Active"), default=False)
    exclude_from_navigation = models.BooleanField(_(u"Exclude from navigation"), default=False)
    exclude_from_search = models.BooleanField(_(u"Exclude from search results"), default=False)

    creator = models.ForeignKey(User, verbose_name=_(u"Creator"), null=True)
    creation_date = models.DateTimeField(_(u"Creation date"), auto_now_add=True)
    modification_date = models.DateTimeField(_(u"Modification date"), auto_now=True, auto_now_add=True)
    publication_date = models.DateTimeField(_(u"Publication date"), default=datetime.datetime.now())

    meta_keywords = models.TextField(_(u"Meta keywords"), blank=True, default="<title>")
    meta_description = models.TextField(_(u"Meta description"), blank=True, default="<title>")

    allow_comments = models.PositiveSmallIntegerField(_(u"Commentable"),
        choices=ALLOW_COMMENTS_CHOICES, default=ALLOW_COMMENTS_DEFAULT)

    def get_absolute_url(self):
        page = self.standard or self

        if settings.LFC_TRAVERSING:
            obj = page
            slugs = []
            while obj is not None:
                slugs.append(obj.slug)
                obj = obj.parent

            slugs.reverse()

            slug =  "/".join(slugs)
        else:
            slug = page.slug

        if page.language == settings.LANGUAGE_CODE:
            return ("lfc_base_view", (), {"slug" : slug})
        elif page.language == "0":
            language = translation.get_language()
            if language == settings.LANGUAGE_CODE:
                return ("lfc_base_view", (), {"slug" : slug})
            else:
                return ("lfc_base_view", (), {"slug" : slug, "language" : language})
        else:
            return ("lfc_base_view", (), {"slug" : slug, "language" : page.language})

    get_absolute_url = models.permalink(get_absolute_url)

    def form(self, **kwargs):
        """Returns the form for the object.

        Has to be implemented by sub classes.
        """
        raise NotImplementedError, "form has to be implemented by sub classed"

    def get_ancestors(self):
        """Returns all ancestors of the page.
        """
        ancestors = []
        page = self
        while page.parent is not None:
            temp = page.parent
            temp = temp.get_specific_type()
            ancestors.append(temp)
            page = page.parent

        return ancestors

    def get_reverse_ancestors(self):
        """Returns all ancestors of the page in reverse order.
        """
        ancestors = self.get_ancestors()
        ancestors.reverse()
        return ancestors

    def get_sub_objects(self):
        """Returns sub objects of an object.
        """
        return self.sub_objects.filter(
            active = True,
            language__in = (translation.get_language(), "0"),
        )

    def get_image(self):
        """Returns the first image of the page.
        """
        images = self.images.all()
        try:
            return images[0]
        except IndexError:
            return None

    def get_meta_keywords(self):
        """Returns the meta keywords of the page.
        """
        keywords = self.meta_keywords.replace("<title>", self.title)
        keywords = keywords.replace("<tags>", self.tags)
        return keywords

    def get_meta_description(self):
        """Returns the meta description of the page.
        """
        description = self.meta_description.replace("<title>", self.title)
        description = description.replace("<tags>", self.tags)
        return description

    def get_template(self):
        """Returns the selected template.
        """
        if self.template is not None:
            return self.template
        else:
            template = lfc.utils.registration.get_default_template_for(self)
            if template is not None:
                return template
            else:
                return lfc.utils.get_portal().get_template()

    def get_title(self):
        """
        """
        return self.display_title and self.title or ""

    def is_canonical(self):
        """Returns True if the language of the page is the default language.
        """
        return self.language in (settings.LANGUAGE_CODE, "0")

    def is_translation(self):
        """Returns True if the page is a translation.
        """
        return not self.is_canonical()

    def get_translation(self, language):
        """Returns translation for given language.
        """
        if self.is_canonical() == False:
            return None
        try:
            return self.translations.get(language=language, active=True)
        except BaseContent.DoesNotExist:
            return None

    def are_comments_allowed(self):
        """Returns True if comments for this object are allowed.
        """
        if self.allow_comments == ALLOW_COMMENTS_DEFAULT:
            return self.parent.are_comments_allowed()
        else:
            if self.allow_comments == ALLOW_COMMENTS_TRUE:
                return True
            else:
                return False

    # Contract for django-portlets
    def get_parent_for_portlets(self):
        """Returns the parent for inheriting portlets.
        """
        return self.parent and self.parent.get_specific_type() or lfc.utils.get_portal()

class Page(BaseContent):
    """A page is the foremost object within lfc which shows information to the
    user.
    """
    text = models.TextField(_(u"Text"), blank=True)
    special = models.BooleanField(default=False)

    def form(self, **kwargs):
        """
        """
        from lfc.manage.forms import PageCoreDataForm
        return PageCoreDataForm(**kwargs)

class Image(models.Model):
    """An image. Generates automatically various sizes.

    title
        The title of the image. Used within the title and alt tag
        of the image
    slug
        The URL of the image

    content
        The content object the image belongs to (optional)

    position
        The ord number within the content object

    caption
        The caption of the image. Can be used within the content (optional)

    short_description
        A short description of the image. Can be used within the content
        (optional)

    description
        A long description of the image. Can be used within the content
        (optional)

    image
        The image file.
    """
    title = models.CharField(blank=True, max_length=100)
    slug = models.SlugField()
    content = models.ForeignKey(BaseContent, blank=True, null=True, related_name="images")
    position = models.SmallIntegerField(default=999)
    caption = models.CharField(blank=True, max_length=100)
    short_description = models.TextField(blank=True)
    description = models.TextField(blank=True)
    image = ImageWithThumbsField(_(u"Image"), upload_to="uploads",
        sizes=((60, 60), (100, 100), (200, 200), (400, 400), (600, 600), (800, 800)))

    class Meta:
        ordering = ("position", )

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return ("gallery.views.photo", (), {"slug" : self.slug})
    get_absolute_url = models.permalink(get_absolute_url)

class File(models.Model):
    """A downloadable file.

    title
        The title of the image. Used within the title and alt tag
        of the image
    slug
        The URL of the image

    content
        The content object the file belongs to (optional)

    position
        The ord number within the content object

    description
        A long description of the image. Can be used within the content
        (optional)

    file
        The file.
    """
    title = models.CharField(blank=True, max_length=100)
    slug = models.SlugField()
    content = models.ForeignKey(BaseContent, blank=True, null=True, related_name="files")
    position = models.SmallIntegerField(default=999)
    description = models.CharField(blank=True, max_length=100)
    file = models.FileField(upload_to="files")

    class Meta:
        ordering = ("position", )

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("lfc_file", kwargs={"id" : self.id})

#### Portlets
###############################################################################

class NavigationPortlet(Portlet):
    """A portlet to display navigation.
    """
    start_level = models.IntegerField(default=1)

    def render(self, context):
        """Renders the portlet as html.
        """
        page = context.get("lfc_object")
        pages = Page.objects.filter(
            parent=page,
            active=True,
            exclude_from_navigation=False,
            language__in=("0", translation.get_language()))

        if len(pages) or page.parent:
            show = True
        else:
            show = False

        request = context.get("request")
        return render_to_string("lfc/portlets/navigation_portlet.html", RequestContext(request, {
            "start_level" : self.start_level,
            "page" : page,
            "show" : show,
            "title" : self.title,
        }))

    def form(self, **kwargs):
        """
        """
        return NavigationPortletForm(instance=self, **kwargs)

class NavigationPortletForm(forms.ModelForm):
    """
    """
    class Meta:
        model = NavigationPortlet

class PagesPortlet(Portlet):
    """A portlet to display pages.
    """
    quantity = models.IntegerField(default=5)
    tags = models.CharField(blank=True, max_length=100)

    def __unicode__(self):
        return "%s" % self.id

    def render(self, context):
        """Renders the portlet as html.
        """
        pages = BaseContent.objects.filter(
            active = True,
            language__in=("0", translation.get_language()))

        if self.tags:
            pages = tagging.managers.ModelTaggedItemManager().with_all(self.tags, pages)[:self.quantity]
        else:
            pages = []

        return render_to_string("lfc/portlets/pages_portlet.html", {
            "title" : self.title,
            "pages" : pages,
        })

    def form(self, **kwargs):
        """
        """
        return PagesPortletForm(instance=self, **kwargs)

class PagesPortletForm(forms.ModelForm):
    """
    """
    class Meta:
        model = PagesPortlet

class RandomPortlet(Portlet):
    """A portlet to display random pages.
    """
    tags = models.CharField(blank=True, max_length=100)
    limit = models.IntegerField(default=1)

    def render(self, context):
        """Renders the portlet as html.
        """
        items = Page.objects.filter(
            language__in=("0", translation.get_language()))

        items = list(items)
        random.shuffle(items)

        return render_to_string("lfc/portlets/random_portlet.html", {
            "title" : self.title,
            "items" : items[:self.limit],
        })

    def form(self, **kwargs):
        """Returns the form of the portlet.
        """
        return RandomPortletForm(instance=self, **kwargs)

class RandomPortletForm(forms.ModelForm):
    """Form for the RandomPortlet.
    """
    class Meta:
        model = RandomPortlet

class TextPortlet(Portlet):
    """A simple portlet to display some text.
    """
    text = models.TextField(_(u"Text"), blank=True)

    def __unicode__(self):
        return "%s" % self.id

    def render(self, context):
        """Renders the portlet as html.
        """
        return render_to_string("lfc/portlets/text_portlet.html", {
            "title" : self.title,
            "text" : self.text
        })

    def form(self, **kwargs):
        """
        """
        return TextPortletForm(instance=self, **kwargs)

class TextPortletForm(forms.ModelForm):
    """Form for the TextPortlet.
    """
    class Meta:
        model = TextPortlet

def register_portlets(sender, **kwargs):
    # don't register our portlets until the table has been created by syncdb
    if sender == portlets.models:
        register_portlet(NavigationPortlet, "Navigation")
        register_portlet(PagesPortlet, "Pages")
        register_portlet(RandomPortlet, "Random")
        register_portlet(TextPortlet, "Text")
post_syncdb.connect(register_portlets)

from lfc.utils.registration import register_content_type
register_content_type(Page, name="Page", sub_types=["Page"], templates=["Article", "Plain", "Gallery", "Overview"], default_template="Article")
