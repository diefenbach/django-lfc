=========
Workflows
=========

General
=======

A workflow consists of a sequence of connected (through transitions) states. 
The transitions can be restricted by permissions.

A workflow can be assigned to models and model instances. All instances will
"inherit" the workflow of its model. If an instance has an own workflow this 
will have precedence. In this way all instances of a content type have the 
same workflow unless a specific instance of that content type have an other 
workflow assigned.

Every workflow manages a set of permissions. Every workflow state can grant
or remove this permissions from the instance for several roles. In this way
objects have different permissions per workflow state.

Simple workflow
===============

A simple workflow for smaller sites where only one or a few authors add 
content objects.

A common workflow cycle would be:

* An user creates a content object. Only the *Owner*, *Editors* and 
  *Managers* can view the content object.
* The *Owner* publishes the object. Users can view the content object.

Portal workflow
===============

A workflow for larger sites where content is provided by several authors.
Every content object must be submitted for review before it can be published. 

A common workflow cycle would be:

* An user creates a content object. Only the *Owner*, *Editors* and 
  *Managers* can view the content object.
* The *Owner* submits the content object for review.
* A *Reviewer* publishes the content object. Users can view the content object.

.. seealso::

   * :doc:`roles`
   * :doc:`permissions`