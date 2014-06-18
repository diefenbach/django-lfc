# django imports
from django import forms


class WYSIWYGInput(forms.Textarea):
    """Widget to display a Textarea with a WYSIWYG editor.
    """
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {"class": "wysiwyginput"}
        if attrs.get("class"):
            attrs["class"] += " wysiwyginput"
        else:
            attrs["class"] = "wysiwyginput"

        output = super(WYSIWYGInput, self).render(name, value, attrs)
        return output + """<script>$(function() { addEditor("#id_%s"); })</script>""" % name
