What is it?
===========

LFC is a Content Manangement System based on Django

Documentation:
==============

* http://packages.python.org/django-lfc

Demo
====

* http://demo.django-lfc.com

Group
=====

* http://groups.google.com/group/django-lfc

Code
====

* http://bitbucket.org/diefenbach/django-lfc

Changes
=======

1.0 alpha 8 (2010-04-16)
------------------------

* Added: Roles
* Added: global_addable to "register_content_type" function
* Improved management: added user management forms
* Improved management: added workflow management forms
* Improved management: take care of permissions
* Improved management: cleaned up permissions forms
* Bugfix: Display only objects with registered content type

1.0 alpha 7 (2010-03-22)
------------------------
* Added workflows and permissions

1.0 alpha 6 (2010-02-14)
------------------------

* Improved manage translations: added automatically slug
* Improved management filebrowser: show global files
* Improved management: delete files/images on file system if an object is deleted
* Improved management: optimized update images
* Improved management: nicer mass uploads for files (same as images)
* Improved search form: take correct slug according to current language for search results
* Improved HTML: Display page titles within title tag
* Gallery template: display image titles
* Update german translations

1.0 alpha 5 (2010-02-01)
------------------------

* Improved getting of specific content objects
* Improved tests and documentation
* Added some caching
* Added cut/copy'n paste within children tabs

1.0 alpha 4 (2010-01-26)
------------------------

* Added methods to unregister content/templates
* Added application installer
* Added cut/copy'n paste
* Added more docs

1.0 alpha 3 (2010-01-22)
------------------------

* A lot of cleanups and bugfixes
* Added on-the-fly template selection
* Added children tab for portal and content objects
* Added new logo
* Added some tests and docs
* Improved file-/imagebrowser
* Removed hard coded path to templates
* Removed tags from portal

1.0 alpha 2 (2010-01-15)
------------------------

* A lot of cleanups and bugfixes
* Added middleware to traverse objects
* Added custom object manager to handle permissions (very simple yet)
* Added simple form to manage registered content types
* Added global images
* Added some docs
* Improved multi languages handling
* Improved object actions
* Improved search
* Updated german translations

1.0 alpha 1 (2010-01-10)
------------------------

* Initial public release