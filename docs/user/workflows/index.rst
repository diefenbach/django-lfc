=========
Workflows
=========

This section describes the workflow management of LFC.

Delete a workflow
=================

To delete a workflow click on the "Delete workflow"-button and answer the 
confirmation dialog with yes.

If you delete a workflow following will take place:

* All content types which have selected this workflow now has no workflow 
  anymore.

* All objects of this content types (which has no own workflow) have no
  workflow (and no workflow state) anymore. All object will keep the current 
  permissions, though

Add a workflow
==============

To add a workflow proceed as following: 

1. Click on the "Add workflow"-button
2. Fill in the unique name 
3. Click on the "Add"-button

Now go through the tabs (see below) and enter additional data, states and 
transitions.

Data
====

Name
    The unique name of the workflow.

Initial state
    This state is assigned to all new content objects which have this 
    workflow.

Permissions
    The set of permission for which the workflow is responsible. This permissions
    can be granted or removed per workflow state
    
States
======

This tab displays all states of the workflow. To edit one just click on it.

Add a state
-----------

To add a state, enter the name and click on the "Add state"-button. After 
that click on the new state and fill in additional information (see below for 
an explanation of the fields).

Delete a state
--------------

To delete a state click on the red cross on the left side of the state and 
answer the confirmation dialog with "yes".

If you delete a state following will take place:

Data
----

Name
    The unique name of the state. This will be displayed on the object.
    
Transitions
    All selected transitions are provided if an object is within the state and
    the current user has the adequate permissions.
    
Type
    If public is checked the object's publication date is set the first time
    the object gets this state
    
    If review is checked the object is displayed within the review list if the
    object is within this state.
    
Permissions
    The permissions for this state. All objects will get this permissions if
    they are in this state.
    
Transitions
===========

This tab displays all transitions of the workflow. To edit one click on it.

Add a transition
----------------

To add a transition, enter the name and click on the "Add transition"-button. 
After  that click on the new transition and fill in additional information 
(see below for an explanation of the fields).

Delete a transition
-------------------

To delete a transition click on the red cross on the left side of the
transition and answer the confirmation dialog with "yes".

Name
    The unique name of the transition. This will be displayed on the object.

Destination 
    The destination state of the transition. If the transition is executed. 
    The object will get this state.

Permission
    The user must have this permission in order to see and execute this 
    transition.

Condition
    The condition must be True in order to display the transition to the 
    current user (not implemented yet).

Roles
    The roles the user must have in order to see and execute this transition.
    (Not implemented yet)
    
.. seealso::

    * :ref:`Workflow concepts <concepts-workflow-label>`

    