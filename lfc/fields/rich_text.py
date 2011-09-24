# django imports
from django import forms
from django.db import models
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.forms import fields

# markdown imports
import markdown


class FormRichTextField(fields.CharField):
    def clean(self, value):
        return value


class RichText(object):
    """
    RichText consists on a plain text and a rendered text which is dendend on
    the text type.
    """
    def __init__(self, text, text_rendered=None, text_type=1):
        self.text = text
        self.text_type = text_type
        if text_rendered is not None:
            self.text_rendered = text_rendered
        else:
            self.text_rendered = self.render_text()

    def render_text(self):
        """
        Renders the text based on the text type.
        """
        if self.text_type == 1:
            return markdown.markdown(self.text)
        else:
            return self.text


class RichTextarea(forms.Textarea):
    """
    Widget to render a RichTextField.
    """
    def render(self, name, value, attrs=None):
        if isinstance(value, RichText):
            text_type = value.text_type
            value = value.text
        else:
            value = ""
            text_type = ""

        options = "<script>$(function() {"
        if text_type in [0, None]:
            options += """addEditor("#id_%s");""" % name
        options += """$("#id_text_type").parents(".field").hide()})</script><select id="id_text_type" name="%s_type" style="display:block; margin-bottom:10px">""" % name

        for option in [[0, "HTML"], [1, "Markup"]]:
            if option[0] == text_type:
                options += """<option selected="selected" value="%s">%s</option>""" % (option[0], option[1])
            else:
                options += """<option value="%s">%s</option>""" % (option[0], option[1])

        options += "</select>"

        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(u'%s<textarea%s>%s</textarea>' % (options, flatatt(final_attrs), conditional_escape(force_unicode(value))))


class RichTextCreator(object):
    """
    RichText descriptor to get/set RichText out of stored/given values.
    """
    def __init__(self, field):
        self.field = field
        self.rendered_name = _rendered_name(self.field.name)
        self.type_name = _type_name(self.field.name)

    def __get__(self, obj, type=None):
        rich_text = RichText(
            text=obj.__dict__[self.field.name],
            text_rendered=obj.__dict__[_rendered_name(self.field.name)],
            text_type=obj.__dict__[_type_name(self.field.name)],
        )

        return rich_text

    def __set__(self, obj, value):
        if isinstance(value, RichText):
            obj.__dict__[self.field.name] = value.text
            setattr(obj, self.rendered_name, value.render_text())
            setattr(obj, self.type_name, value.text_type)
        else:
            obj.__dict__[self.field.name] = self.field.to_python(value)


class RichTextField(models.TextField):
    """
    A text field which stores original text and a rendered text based on text
    type.
    """

    description = "A text field which can handle text and rendered text"

    def __init__(self, *args, **kwargs):
        super(RichTextField, self).__init__(*args, **kwargs)

    def get_db_prep_save(self, value):
        if isinstance(value, RichText):
            value = value.text
        return super(RichTextField, self).get_db_prep_save(value)

    def contribute_to_class(self, cls, name):
        text_rendered = models.TextField(blank=True)
        text_rendered.creation_counter = self.creation_counter
        cls.add_to_class(_rendered_name(name), text_rendered)

        text_type = models.PositiveSmallIntegerField(blank=True, null=True)
        text_type.creation_counter = self.creation_counter + 1
        cls.add_to_class(_type_name(name), text_type)

        super(RichTextField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, RichTextCreator(self))

    def formfield(self, **kwargs):
        defaults = {
            'widget': RichTextarea,
            "form_class": FormRichTextField,
        }
        defaults.update(kwargs)
        return super(RichTextField, self).formfield(**defaults)


def _rendered_name(name):
    return "%s_rendered" % name


def _type_name(name):
    return "%s_type" % name
