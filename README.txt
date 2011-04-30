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

* http://bitbucket.org/diefenbach/django-lfc

Changes
=======

1.0.4 (2011-04-30)
------------------

Bugfix release

* Bugfix: Removed mutuable parameters; issue #11 of django-permissions

1.0.3 (2011-04-10)
------------------

Bugfix release

* Bugfix: delete assigned portlets after an object has been deleted
* Bugfix: templatetag 'navigation': check whether there is a 'get_ancestors' method; issue #25
* Bugfix: invalidate cache after images has been updated or added; issue #50
* Bugfix: prevent to add same Users several times to a Role; issue #6 of django-workflows
* Bugfix: DatabaseErrors with Postgres; issue #5 of django-permissions
* Bugfix: changed order of passed parameters to has_permission; issue #6 of django-permissions
* Bugfix: removed not needed import of "sets"; issue #8 of django-permissions

1.0.2 (2010-10-16)
------------------

Bugfix release

* Fix for issue #43: User needs permission 'manage_content' in order to change creator
* Fix for issue #44: Take care of user's permissions within children tab
* Fix for issue #45: Delete Portlet within delete_portlet (not only PortletAssignment)
* Bugfix: Corrected several needed permissions for cut/copy'n paste
* Don't display paste button, if the user hasn't the right permission

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

First final release

* Bugfix management: access to jsi18n; issue #33