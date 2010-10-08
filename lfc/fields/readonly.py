# django imports
from django import forms
from django.contrib.auth.models import User

class ReadOnlyInput(forms.HiddenInput):
    """Widget to only display fields value.
    """
    def render(self, name, value, attrs=None):
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            return ""
        if user.first_name and user.last_name:
            username = user.first_name + " " + user.last_name
        else:
            username = user.username

        html = """<input type="hidden" name="%s" value="%s">%s""" % (name, user.id, username)
        return html