========
Overview
========

LFC is aimed to be small, uncomplicated and fast for both: users and 
developers.

Content types
-------------

Within the core of LFC there is only one :term:`content type`: :term:`Page` 
(more can be added by 3rd-party developers).

Every instance of a page can have arbitrary sub pages (this will build the
content structure).

Templates
---------

The content of a page is displayed by templates. By default there are just
a small bunch of templates (more can be added by 3rd-party developers):

    - Plain

      Only the text is displayed: The user can add images by the WYSIWYG
      Editor

    - Article

      The first assigned image is displayed top left, the text flows around
      the image.

    - Gallery

      All assigned images are display as gallery (lightbox style)

    - Overview

      All assigned sub pages are displayed as a list

Images and Files
----------------

Every page can have an arbitrary amount of images and files. How they are
displayed is up to the selected template.

Portlets
--------

Every page can have so-called :term:`portlets`, which are displayed in a left 
or a right slot. By default there are just a few portlets (more can be added 
by 3rd-party developers):

    - Text portlet

      A portlet to display HTML structured text

    - Navigation portlet

      A portlet to display the content structure as navigation tree

    - Pages

      A portlet to display selected (by tags) pages

Portlets are inherited from parent pages but it is also possible to block 
parent portlets per :term:`slot`.

Multi-languages
---------------

Every page can have multiple languages.

By default all new pages are created in the default language and all 
translations are assigned automatically to the base canonical object, but
it is also possible to create completely independent page structures in
different languages

Additionally it is possible to create language neutral objects which are 
displayed independent on the current language.