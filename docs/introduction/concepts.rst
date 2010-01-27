========
Concepts
========

Content types
-------------

Within the core of LFC there is only one :term:`content type`: :term:`Page`
(more can be added by developers).

Sub objects
-----------

Every instance of an content object can have arbitrary sub objects which will
build the content structure. Every content type can restrict the type of
allowed sub types, though.

Images and Files
----------------

Every object can have an arbitrary amount of images and files. How they are
displayed is up to the selected template.

Templates
---------

The content of an object is displayed by :term:`templates`. By default there 
are  just a small bunch of templates (more can be added by developers):

* Plain

  Only the text is displayed: The user can add images by the WYSIWYG
  Editor

* Article

  The first assigned image is displayed top left, the text flows around
  the image.

* Gallery

  All assigned images are display as a 3x3 grid.

* Overview

  All assigned sub objects are displayed as a list. The first image of the
  sub objects (if there is one) is displayed.

Portlets
--------

Every object can have so-called :term:`portlets`, which are displayed in a 
:term:`slots`. By default there is a left and a right slot and  just a few 
portlets (more slots and portlets can be added by developers):

* Text portlet

  A portlet to display HTML structured text

* Navigation portlet

  A portlet to display the content structure as navigation tree

* Pages

  A portlet to display selected (by tags) pages

Portlets are inherited from parent pages but it is also possible to block
parent portlets per :term:`slot`.

Translations
------------

Every page can have multiple translations.

By default all new pages are created in the default language and all
translations are assigned automatically to the base canonical object, which has
the advantage that the user is automatically redirected to the correct 
translation if he changes the language. But it is also possible to create 
completely independent page structures in different languages.

Additionally it is possible to create language neutral objects which are
displayed independent on the current selected language.