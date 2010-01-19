=================
Create a template
=================

In order to create a LFC template you just have to create a default Django 
template and register it to the models you want to use it.

Within your existing Django application create a folder called "templates". Your
folder structure should now looks like this::

    lfc_events
        __init__.py
        models.py
        templates
        
Now create a file called event_1.html within the templates folder and add these
lines of code:

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
    
Register the template
=====================

In order to register the template just add the following lines to your 
models.py

.. code-block:: python
    :linenos:

    from lfc.utils.registration import register_template
    register_template(name = "Event 1", file_name="lfc_events/event_1.html")

1: 
    Import the utility method to register a template.
2:
    Register the template with name "Event 1".

Create another template
=======================

Now create another template "Event 2" and register it.