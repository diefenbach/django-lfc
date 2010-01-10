What is it?
===========

LFC is a Content Manangement System based on Django

Features:
=========

- Variable templates to view the content
- Variable portlets
- Multi languages (without pain)
- Bulk upload of image
- Automatic scaling of images
- WYSIWYG-Editor
- Tagging
- Commenting
- RSS Feeds
- Pluggable (Write content types and portlets)

Installation
=============

0. Install mercurial

   $ easy_install mercurial"

1. Get the buildout

   hg clone http://bitbucket.org/diefenbach/lfc-buildout-development/

2. Execute the buildout

   a. $ cd lfc-buildout-development
   b. $ python boostrap
   c. $ bin/buildout -v

3. Start the server
   $ bin/django runserver

4. Login

   http://localhost:8000/login/ (admin/admin)

5. Go to the management interface

   http://localhost:8000/manage/

Changes
=======

1.0 alpha 1 (2010-01-10)
------------------------

* Initial public release