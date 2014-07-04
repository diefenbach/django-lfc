What is it?
===========

LFC is a Content Manangement System based on Django

Demo
====

* http://demo.django-lfc.com

Group
=====

* http://groups.google.com/group/django-lfc

Code
====

* http://github.com/diefenbach/django-lfc

Changes
=======

1.2b1 (2014-07-04)
------------------

* Updates 3rd party javascripts (jquery, jquery ui, tinymce, superfish, etc.)
* Adds progress bar to image uploads
* Removes dependencies from django admin (uses own date/time picker)
* Improves manage tabs (removes flicker)
* Fixes lightbox for django-compressor (unicode decode error)
* Moves static files to own namespaces (folders)

1.1.1 (2014-06-27)
------------------

* Adds Pillow to ``install_requires``
* Adds django-compressor to ``install_requires``
* Fixes german translation for lfc-contact-form


1.1 (2014-06-26)
----------------

* Adds Django 1.6 support
* Factores out page content type to lfc-page
* Factores out portlets to lfc-portlets
* Factores out contact form to lfc-contact-form
