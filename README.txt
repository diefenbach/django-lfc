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

1.0.1 (2010-09-21)
------------------

Bugfix release

* Fix for issue #34: Make removing of dates (within Metadata tab) possible
* Fix for issue #35: Don't require "manage_portal"-permission to change
  languages within management UI
* Fix for issue #36: Typo in object_permissions.html
* Fix for issue #37: Password change form: change password of selected user
  (not current logged-in user)

1.0 (2010-08-24)
----------------

* First final release
* Bugfix management: access to jsi18n; issue #33

1.0 beta 5 (2010-07-23)
-----------------------

* Added dependencies to setup.py
* Filebrowser: cleaned up appearance

1.0 beta 4 (2010-07-23)
-----------------------

* Added detailed access control
* Added date time picker to date fields in manage forms. Issue #12
* Changed: order permissions alphabetical by name
* Bugfix add form: Don't try to get local files. Issue #26
* Bugfix Portal.get_absolute_url: using url lfc_base_view. Issue #28
* Bugfix RSS feeds: make them work again

1.0 beta 3 (2010-07-07)
-----------------------

* Added: lfc_init management commands
* Changed: using own contact form in order to use portal emails; 
  Moved contact urls from lfc_project/urls.py to lfc/urls.py
* Changed: cache keys are using CACHE_MIDDLEWARE_PREFIX now (Maciej
  Wisniowski)
* Bugfix caching: added language to cache key
* Bugfix portlets. Show error if add/edit form doesn't validate. Issue #16
* Bugfix: do not allow to upload images if content is not yet created. Issue #18 
  (Maciej Wisniowski)
* Bugfix mass uploading: added missing element with id=divStatus to display 
  upload completed status; hide it via CSS for now; Issue #13
* Bugfix Management panel: IE7 problem. Issue #20
* Bugfix views.save_workflow_data: removed except IntegrityError. Issue #15
* Bugfix BaseContent.get_allowed_transitions: removed obj parameter from call 
  to self.has_permission()
* Fixed some typos. Issue #17

1.0 beta 2 (2010-05-21)
-----------------------

* Improved caching
* Added License
* Moved LANGUAGES_DICT and LFC_LANGUAGE_IDS from django settings to lfc settings

1.0 beta 1 (2010-05-17)
-----------------------

* Improvement: speeded up copy'n paste
* Added: date dependent publishing
* Added: image browser; Added link to original image
* Added: management; added optional simplification by settings
* Added: management; added menu to change general language
* Added: creation date to Image and File
* Bugfix: view portal without standard page
* Bugfix: calculation of children positions
* Bugfix: deleting related workflows and permissions information when deleting content objects
* Bugfix: display only published objects within navigation portlet
* Bugfix: set publication date when change workflow state within preview
* Bugfix: remove WorkflowModelRelation if an application is uninstalled
* Bugfix: management portal; display correct message if an error occured. Issue #8
* Bugfix: management; allow only unique slugs
* Bugfix: postgreSQL: get comments of an object
* Bugfix: postgreSQL; factored out initial registering to scripts. issue #1
* Bugfix: filebrowser; display local images

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