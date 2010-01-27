============
Translations
============

LFC provides multi languages for the content. Here is a short description on
how to use it and how it works.

Preparations
============

In order to use multi languages it has to be turned on. To do that please 
add/edit following settings within your settings.py::

  LANGUAGE_CODE = 'en'
  LANGUAGES = (("en", _(u"English")), ("de", _(u"German")))

Whereas LANGUAGE_CODE (which is a default Django setting) is the default 
language (all objects will be created with this one) and LANGUAGES are all 
available languages. There must be at least two languages to turn the multi
language feature on.

Create a translation
====================

In order to create a translation browse to the object and select the lanuage
you want from the "Translate to" Menu. 

.. image:: /images/translations_1.*

Fill in the form and click the "Save" button.

**Now following has taken place:**

* The translation in the selected language has been created, i.e.: the created 
  content object has the language you choosed above.
* The translation has been assigned to the source object (see the "canonical" 
  field of the "Metadata" tab), which means that the user is redirected to the
  connected object in the right language if he changes the language.
  
Change between translations
===========================

If translations exist for an object you will see the languages menu. With 
the help of that you see the current language (in this case: "English") and 
you can switch to all existing languages (in this case: "English" and 
"German").

.. image:: /images/translations_2.*

The same is true for the navigation tree.

.. image:: /images/translations_3.*


Site strucutures
================

As you have seen the source object and the translations are connected 
automatically to each other. 

But you can change or remove this connections completely. In this way it is 
possible to create completely independent site structures in different 
languages. For that go to the "Metadata" tab and change or remove the 
"canonical" field of the object.

Neutral objects
===============

It is also possible to add language neutral objects. These objects are
displayed for every language. For that, go to the "Metadata" tab and change
the language to neutral.