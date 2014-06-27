# python imports
import json

# django imports
from django import forms
from django.utils.safestring import mark_safe

# tagging imports
from tagging.models import Tag


class AutoCompleteTagInput(forms.TextInput):
    def render(self, name, value, attrs=None):
        output = super(AutoCompleteTagInput, self).render(name, value, attrs)
        tags = Tag.objects.all()
        tag_list = json.dumps([tag.name for tag in tags], ensure_ascii=False)
        return output + mark_safe(u'''<script type="text/javascript">
            function split( val ) {
              return val.split( /,\s*/ );
            }
            function extractLast( term ) {
              return split( term ).pop();
            }

            $( "#id_%s" )
              // don't navigate away from the field on tab when selecting an item
              .bind( "keydown", function( event ) {
                if ( event.keyCode === $.ui.keyCode.TAB &&
                    $( this ).autocomplete( "instance" ).menu.active ) {
                  event.preventDefault();
                }
              })
              .autocomplete({
                minLength: 0,
                source: function( request, response ) {
                  // delegate back to autocomplete, but extract the last term
                  response( $.ui.autocomplete.filter(
                    %s, extractLast( request.term ) ) );
                },
                focus: function() {
                  // prevent value inserted on focus
                  return false;
                },
                select: function( event, ui ) {
                  var terms = split( this.value );
                  // remove the current input
                  terms.pop();
                  // add the selected item
                  terms.push( ui.item.value );
                  // add placeholder to get the comma-and-space at the end
                  terms.push( "" );
                  this.value = terms.join( ", " );
                  return false;
                }
              });
          </script>''' % (name, tag_list))
