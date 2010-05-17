=========================
Create an own application
=========================

In this tutorial you will learn how to create a complete simple application
for LFC. It assumes that you are familiar with Python and Django.

You can :download:`download the whole application here <lfc_events.tar.gz>`.

Preparations
============

First you have to create a new Django application. This is beyond the purpose
of this tutorial and you should refer to `Django's excellent tutorial <http://docs.djangoproject.com/en/dev/intro/tutorial01/>`_ 
if you want to learn more. 

In short, your starting file structure should look like this::

    lfc_events
        __init__.py
        models.py

For an easier start you can also use `lfc-skel <http://pypi.python.org/pypi/lfc-skel>`_.
See there on how to install it.

Content type
=============

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
    The new content type. It Inherits from BaseContent.

14/15:

    Adds default Django fields to the content type, in this case two date/time
    fields.

17-20
    The form method is the only method which has to be implemented by a LFC
    content type. It has to return the form to add/edit the related content
    type.

22-27
    Default Django model form to add/edit the Event type.

Template
========

In order to create a LFC template you just have to create a default Django
template and register it to the models you want to use it.

Within your existing Django application create a folder called "templates" and
then a folder called "lfc_events". Your folder structure should now looks like
this::

    lfc_events
        __init__.py
        models.py
        templates
            lfc_events

Now create a file called event_1.html within the lfc_events folder and add
these lines of code:

.. code-block:: html
    :linenos:

    {% extends "lfc/base.html" %}

    {% block content %}
        <h1>Event 2</h1>

        <h2>
            Start
        </h2>
        <p>
            {{ lfc_context.start }}
        </p>

        <h2>
            End
        </h2>
        <p>
            {{ lfc_context.end }}
        </p>
    {% endblock %}

1:
    Extends the LFC base template

3:
    Fill the block content of the base template

10/17:

    lfc_context is the current viewed content object. "start" and "end" are
    the fields we added to our content object.

Now create another template in the same way and call it "Event 2".

Portlet
=======

In order to create a own portlet you need to create two parts: The python
part, which contains the portlet class and the template to present the portlet
as HTML.

**Create the portlet class**

.. code-block:: python
    :linenos:

    # django-portlets imports
    from portlets.models import Portlet

    class EventsPortlet(Portlet):
        """A simple portlet to display Events.
        """

        limit = models.IntegerField(blank=True, null=True)

        def render(self, context):
            """Renders the content of the portlet.
            """
            obj = context.get("lfc_context")
            request = context.get("request")

            events = Event.objects.restricted(request).order_by("start")[:self.limit]

            return render_to_string("lfc_events/events_portlet.html", {
                "title" : self.title,
                "events" : events,
            })

        def form(self, **kwargs):
            """Returns the add/edit form of the EventPortlet
            """
            return EventsPortletForm(instance=self, **kwargs)

    class EventsPortletForm(forms.ModelForm):
        """Form to add / edit an EventPortlet.
        """
        class Meta:
            model = EventsPortlet

2:
    Import the portlet base class. All portlets should inherit from it.

4:
    The new portlet. Inherits from BaseContent.

8:
    Adds default Django fields to the portlet, in this case an integer field
    to limit the amount displayed events.

10:
    The render method must be implemented. It must return the rendered HTML
    content of the portlet.

13:
    Gets the current object, which is always within context.get("lfc_context")

14:
    Gets the request, which is always within context.get("request")

17:
    Gets all events limited by the stored limit attribute. Please note, we
    using the restricted method of the manager here in order to get only
    active events (for anonmyous users).

24:
    The form method must be implemented. It must resturn the form to add /
    edit the portlet.

29:
    Default Django model form to add/edit the Events portlet.

**Create the portlet template**

Create a file called "events_portlet.html" within the template folder and
add the following HTML code:

.. code-block:: html
    :linenos:

    {% extends "lfc/portlets/base.html" %}

    {% block portlet_name %}events{% endblock %}
    {% block body %}
        {% for event in events %}
            <div>
                <a href="{{ event.get_absolute_url }}">
                    {{ event.title }}
                </a>
            </div>
            <div align="right">
                {{ event.start }}
            </div>
        {% endfor %}
    {% endblock %}

1:
    Reusing LFC's base template for portlets

3:
    Fill the block "portlet_name" with the name of the portlet. This can be
    used within CSS to provide specific formats for the EventsPortlet.

4:
    Fill the block "body" with the content of the portlet.

Registration
============

At last we have to provide an install method which registers all the
components.

For that go to the __init__.py of your application and add an install method
like following:

.. code-block:: python
    :linenos:

    # lfc imports
    from lfc.utils.registration import register_content_type
    from lfc.utils.registration import unregister_content_type
    from lfc.utils.registration import register_template
    from lfc.utils.registration import unregister_template

    # portlets imports
    from portlets.utils import register_portlet
    from portlets.utils import unregister_portlet

    # lfc_events import
    from lfc_events.models import Event
    from lfc_events.models import EventsPortlet

    def install():
        register_template(name = "Event 1", path="lfc_events/event_1.html")

        register_content_type(obj = Event, name = "Event",
            templates=["Event 1"], default_template="Event 1")

        register_portlet(EventsPortlet, "Events")

1-13:
    Import all the stuff we need for registration

15:
    The install method. This *must* exist in order to install a application for
    LFC.

16:
    Register the template with name "Event 1".

18/19:
    Registers the content type to LFC's model registration, which means in this
    case:

    * We register the model Event under the name "Event".
    * An Event has two possible templates from which the user can choose:
      "Event 1" and "Event 2" (which has to be written yet).
    * The default template is "Event 1".

21:
    Registers the portlet with name "Events".

Unregistration
==============

To be a good LFC citizen we provide also an uninstall method which removes all
the stuff we have added.

.. code-block:: python
    :linenos:

    def uninstall():
        # unregister content type
        unregister_content_type("Event")

        # unregister templates
        unregister_template("Event 1")
        unregister_template("Event 2")

        # unregister portlet
        unregister_portlet("Events")
