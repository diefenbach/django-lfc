========
Concepts
========

This section describes shortly the concepts of LFC. You will find more 
detailed information later in this documentation.

Content types
=============

Within the core of LFC there is only one :term:`content type`: :term:`Page`
(more can be added by developers).

Sub objects
===========

Every instance of an content object can have arbitrary sub objects which will
build the content structure. Every content type can restrict the type of
allowed sub types.

Images and Files
================

Every object can have an arbitrary amount of images and files. How they are
displayed is up to the selected template.

Templates
=========

The content of an object is displayed by :term:`templates`. By default there 
are  just a small bunch of templates (more can be added by developers):

Plain

  Only the text is displayed: The user can add images with the :term:`WYSIWYG`
  Editor

Article

  The first assigned image is displayed top left, the text flows around
  the image.

Gallery

  All assigned images are display as a 3x3 grid.

Overview

  All sub pages are displayed as a list. The first image of the sub pages 
  (if there is one) is displayed as thumbnail top left, the text flows around
  the image.

Portlets
========

Every object can have so-called :term:`portlets <portlet>`, which are displayed in a 
:term:`slots`. By default there is a left and a right slot and  just a few 
portlets (more slots and portlets can be added by developers):

Text portlet

  A portlet to display HTML structured text

Navigation portlet

  A portlet to display the content structure as navigation tree

Pages

  A portlet to display selected (by tags) pages

Portlets are inherited from parent pages but it is also possible to block
parent portlets per :term:`slot`.

Translations
============

Every page can have multiple translations.

By default all new objects are created in the default language and all
translations are assigned automatically to the base canonical object, which has
the advantage that the user is automatically redirected to the correct 
translation if he changes the language. But it is also possible to create 
completely independent page structures in different languages.

Additionally it is possible to create language neutral objects which are
displayed independent on the current selected language.

Permissions
===========

Permissions are granted to roles (and only to roles) in order to allow 
specific actions (e.g. add content) for users or groups.

.. _concepts-roles-label:

Roles
=====

Roles are used to grant permissions. LFC comes with a several *Roles* by 
default (more can be added by users):

* Anonymous
* Editor
* Manager
* Owner
* Reader
* Reviewer

Local Roles
===========

Local roles are roles which are assigned to users and groups for specific
content objects.

.. _concepts-users-label:

Users
=====

* Users are actors which may need a permission to do something within LFC.
* Users can be members of several groups.
* Users can have several roles, directly or via a membership to a group
  (these are considered as global).
* Users can have *local roles*, directly or via a membership to a group. That is
  roles for a specific object.
* Users have all roles of their groups - global and local ones.
* Users have all permissions of their roles - global and local ones.

.. _concepts-groups-label:

Groups
======

* Groups combines users together.
* Groups can have roles (these are considered as global).
* Groups can have local roles, that is roles for a specific object.
* Groups has all permissions of their roles - global and local ones.
* Users of a Group have the group's roles and permissions.

.. _concepts-workflow-label:

Workflows
=========

A workflow consists of a sequence of connected (through transitions) states. 
The transitions can be restricted by permissions.

By default LFC comes with two workflows (more can be added by users and
developers):

Simple Workflow

    A simple workflow for smaller sites where only one or a few authors add 
    content objects.

Portal Workflow

    A workflow for larger sites where content is provided by several authors.
    Every content object must be submitted for review before it can be 
    published.