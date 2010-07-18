=====
Roles
=====

LFC comes with several roles out of the box.

These roles have several default permissions by default. Anyway, the
permissions can vary dependent on the workflow and workflow state of an
content object.

General
=======

* Every user has automatically the *Anonymous* role.
* The creator of an object has automatically the *Owner* role
* The *Manager* role can do everything independent on workflow and current
  workflow state.
* The *Reviewer* role can change the workflow state of an object independent
  on workflow and current workflow state.

Simple workflow
===============

Anonymous

    Can read public content objects.

Owner

    Can do anything on own content objects, except change permissions.

Editor

    Can do anything on the content object, except change permissions.

Reader

    Can read public content objects.

Manager
    
    Can do everything.

Portal workflow
===============

Anonymous

    Can read public content objects.

Owner

    Can do anything on his own private content objects, except change
    permissions. 
    
    Once the object is submitted or published the owner has to retract the 
    object to be able to modfiy it.    

Editor

    Can do anything on content objects, except change permissions.

Reader

    Can read public content objects.

Reviewer

    Can publish submitted content objects.

Manager
    
    Can do everything.
    
.. seealso::

   * :doc:`permissions`
   * :doc:`workflows`
