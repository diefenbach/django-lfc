============
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

    # register the template
    register_template(name = "Event 1", file_name="lfc_events/event_1.html")

    # register the content type
    register_content_type(obj = Event, name = "Event",
        templates=["Event 1"], default_template="Event 1")

    # register the portlet
    register_portlet(EventsPortlet, "Events")

1-13:
    Import all the stuff we need for registration

16:
    Register the template with name "Event 1".


19/20:
    Registers the content type to LFC's model registration, which means in this
    case:

    * We register the model Event under the name "Event".
    * An Event has two possible templates from which the user can choose:
      "Event 1" and "Event 2" (which has to be written yet).
    * The default template is "Event 1".

23:
    Registers the portlet with name "Events".

==============
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
