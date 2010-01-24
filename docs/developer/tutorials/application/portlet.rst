================
Create a portlet
================

In order to create a own template you need to create two parts: The python 
part, which contains the portlet class and the template to present the portlet
as HTML.

Create the class
================

.. code-block:: python
    :linenos:

    # django-portlets imports
    from portlets.models import Portlet
    from portlets.utils import register_portlet

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

3:
    Import the utility method to register a portlet

5:
    The new portlet. Inherits from BaseContent.

9:
    Adds default Django fields to the portlet, in this case an integer field
    to limit the amount displayed events.

14:
    Gets the current object, which is always within context.get("lfc_context")

15:
    Gets the request, which is always within context.get("request")

11:
    The render method must be implemented. It must return the rendered HTML
    content of the portlet.

17:
    Gets all events limited by the stored limit attribute. Please note, we
    using the restricted method of the manager here in order to get only
    active events (for anonmyous users).

24:
    The form method must be implemented. It must resturn the form to add /
    edit the portlet.

29:
    Default Django model form to add/edit the Events portlet.

Create the template
===================

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
        