from django import forms
from django.db.models import get_model
from django.utils import simplejson
from django.utils.safestring import mark_safe
from tagging.models import Tag

class AutoCompleteTagInput(forms.TextInput):
    class Media:
        css = {
            'all': ('jquery.autocomplete.css',)
        }
        js = (
            'lib/jquery.js',
            'lib/jquery.bgiframe.min.js',
            'lib/jquery.ajaxQueue.js',
            'jquery.autocomplete.js'
        )

    def render(self, name, value, attrs=None):
        output = super(AutoCompleteTagInput, self).render(name, value, attrs)
        tags = Tag.objects.all()
        tag_list = simplejson.dumps([tag.name for tag in tags],
                                    ensure_ascii=False)
        return output + mark_safe(u'''<script type="text/javascript">
            jQuery("#id_%s").autocomplete(%s, {
                width: 150,
                max: 10,
                highlight: false,
                multiple: true,
                multipleSeparator: ", ",
                scroll: true,
                scrollHeight: 300,
                matchContains: true,
                autoFill: true
            });
            </script>''' % (name, tag_list))
            
            
from django import forms
from django.conf import settings
from django.utils.text import truncate_words

class ForeignKeySearchInput(forms.HiddenInput):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a <select> box.
    """
    class Media:
        css = {
            'all': ('jquery.autocomplete.css',)
        }
        js = (
            'lib/jquery.js',
            'lib/jquery.bgiframe.min.js',
            'lib/jquery.ajaxQueue.js',
            'jquery.autocomplete.js'
        )
    
    def __init__(self, instance, attrs=None):
        """
        """
        self.instance = instance
        super(ForeignKeySearchInput, self).__init__(attrs)
        
    def label_for_value(self, value):
        obj = BaseContent.objects.get(id=value)
        return truncate_words(obj, 14)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        rendered = super(ForeignKeySearchInput, self).render(name, value, attrs)

        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        return rendered + mark_safe(u'''
            <input type="text" id="lookup_%(name)s" value="%(label)s" />
            <a href="#" id="del_%(name)s">
            <img src="%(admin_media_prefix)simg/admin/icon_deletelink.gif" />
            </a>
            <script type="text/javascript">
                        if ($('#lookup_%(name)s').val()) {
                            $('#del_%(name)s').show()
                        }
                        $('#lookup_%(name)s').autocomplete('/search', {
                            highlight: false,
                            scroll: true,
                            scrollHeight: 300,
                            matchContains: true,
                            extraParams: {
                                search_fields: '%(search_fields)s',
                                app_label: '%(app_label)s',
                                model_name: '%(model_name)s',
                                page_id : %(instance_id)s,
                            },
                        }).result(function(event, data, formatted) {
                            if (data) {
                                $('#id_%(name)s').val(data[1]);
                                $('#del_%(name)s').show();
                            }
                        });
                        $('#del_%(name)s').click(function(ele, event) {
                            $('#id_%(name)s').val('');
                            $('#del_%(name)s').hide();
                            $('#lookup_%(name)s').val('');
                        });
                        </script>
                    ''') % {
                        'search_fields': "title",                        
                        'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
                        'model_name': "page",
                        'app_label': "lfc",
                        'label': label,
                        'name': name,
                        "instance_id" : self.instance.id,
                    }