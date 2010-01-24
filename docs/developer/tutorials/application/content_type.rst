=====================
Create a content type
=====================

In order to create a own content type you just need to add few lines of code
within models.py

.. code-block:: python
    :linenos:

    # python imports
    import datetime

    # django imports
    from django import forms
    from django.db import models

    # lfc imports
    from lfc.models import BaseContent

    class Event(BaseContent):
        """A simple event type for LFC.
        """
        start = models.DateTimeField(blank=True, default=datetime.datetime.now)
        end = models.DateTimeField(blank=True, default=datetime.datetime.now)

        def form(self, **kwargs):
            """Returns the add/edit form of the Event
            """
            return EventForm(**kwargs)

    class EventForm(forms.ModelForm):
        """Form to add / edit an Event.
        """
        class Meta:
            model = Event
            fields = ("title", "slug", "description", "start", "end")

1-6:
    Default imports from python and django.

9:
    BaseContent is the base class from which all LFC content types should
    inherit.

11:
    The new content type. Inherits from BaseContent.

14/15:

    Adds default Django fields to the content type, in this case two date/time
    fields.

17-20
    The form method is the only method which has to be implemented by a LFC
    content type. It has to return the form to add/edit the related content
    type.

22-27
    Default Django model form to add/edit the Event type.