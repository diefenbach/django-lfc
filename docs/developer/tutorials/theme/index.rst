==============
Create a theme
==============

In this tutorial you will learn how to create a theme for LFC.

You can :download:`download the whole theme here <mytheme.tar.gz>`.

Preparations
============

First you have to create a new Django application. This is beyond the purpose
of this tutorial and you should refer to `Django's excellent tutorial 
<http://docs.djangoproject.com/en/dev/intro/tutorial01/>`_ if you want to learn 
more.

Add a templates folder and within that add a lfc folder.

In short, your starting file structure should look like this::

    mytheme
        __init__.py
        templates
            lfc

Registration
============

Register mytheme to Django's template engine.

1. Move the mytheme folder to the PYTHONPATH.

    The easiest way to do that is to put it into the lfc_project folder of the
    buildout.

2. Register the theme

    Add mytheme to INSTALLED_APPS **before** lfc_theme::

     INSTALLED_APPS = (
         ...
         "mytheme",
         "lfc_theme",
         "django.contrib.admin",
         ...

Copy templates
==============

Now copy the templates you want to change into the lfc folder of mytheme and 
adapt them to your needs.

**Important:** you have to keep the original path, e.g: base.html must be within
the root of the lfc folder whereas navigation_portlet.html must be within the
portlets  folder::

    mytheme
        __init__.py
        templates
            lfc
                base.html
                portlets
                    navigation_portlet.html

Use own CSS
===========

To use own CSS several steps are neccessary (this is going to be improved a lot
for future versions).

1. Create a "static" folder within mytheme::

    mytheme
        static
        ...

2. Within that create a new CSS-file, e.g. mytheme.css and add your CSS rules, e.g.::

    h1.logo a {
        color: #E5AB52 !important;
    }

   Alternatively you might copy lfc.css from lfc_theme and adapt it to your
   needs.

3. Go to the lfc_project/media folder and create a symbolic link to the
   static folder::

   $ ln -s <path/to/buildout>/lfc_project/mytheme/static mytheme

4. Copy base.html to mytheme/templates/lfc (if you haven't done it so far)

5. Include your CSS file to the header::

    <link rel="stylesheet" type="text/css" href="{{ MEDIA_URL }}mytheme/mytheme.css">

6. Optionally delete the link to lfc.css (if you just want to use your own CSS).