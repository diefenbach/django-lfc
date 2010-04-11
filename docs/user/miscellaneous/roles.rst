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

    Can do anything on the content object.

Editor

    Can do anything on the content object.

Reader

    Can read public content objects.

Portal workflow
===============

Anonymous
    
    Can read public content objects.

Owner

    Can do anything on his own private content objects.

Editor

    Can do anything on content objects.

Reader

    Can read public content objects.

Reviewer

    Can do anything on submitted content objects.
