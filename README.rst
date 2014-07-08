Introduction
============

LFC is a Content Management System (CMS) based on widely used software: Python, Django and jQuery. It is easy to use, easy to customize, fast, free and open source.

.. image:: https://travis-ci.org/diefenbach/lfc-installer.svg?branch=version%2F1.2
    :alt: Build Status
    :target: http://travis-ci.org/django-lfc/django-lfc


Documentation
=============

* http://lightning-fast-cms.readthedocs.org

Code
====

* http://github.com/diefenbach/django-lfc

Demo
====

* http://demo.lfcproject.com

Group
=====

* http://groups.google.com/group/django-lfc

Changes
=======

1.2b3 (2014-07-08)
------------------

* Updates django-portlets to 1.3
* Updates lfc-theme to 1.2.1
* Updates Pillow to 2.5.0
* Updates Docs
* Adds tests of dependencies


1.2b2 (2014-07-05)
------------------
* Formats buttons and select boxes with jquery.ui
* Fixes superfish menu after ajax call

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
