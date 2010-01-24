=================
Create a template
=================

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
    
Create another template
=======================

Now create another template "Event 2".