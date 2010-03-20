====
Page
====

This section describes the several data tabs and fields of the page content 
object.

Data
=====

Title
    The title of the page. The title is displayed on top of the page and as 
    within the title tab of the page.

Display Title
    When this is checked the title is displayed on top of the page.

Slug
    The unique URL of the page within the parent page.

Description
    The description of the page. This is used within the overview template and
    search results.

Text
    The main HTML text of a page.

Tags
    The tags of the page. Tags are keywords. This kind of metadata helps
    describe a page and allows it to be found again by browsing or searching.

Metadata
========

.. _template-label:

Template
    The template which is used to display the object's content. Please note: 
    If this field is not displayed just the default template has been 
    registered.

.. _page-standard-label:

Standard
    The sub page which should be displayed instead of the page itself. Please 
    note: If this field is not displayed the page has no sub pages.

Active
    Only active objects are displayed. If an user tries to display an inactive
    objects he gets a page not found disclaimer (404).

Exclude from navigation
    If checked this object is not displayed within the tabs or the navigation
    :term:`portlet`.

Exclude from search results
    If checked this object is not displayed within search results.

Language
    The language of the object.

    .. note::
        
        If this field is not displayed your site has multi languages deactivated.

Publication date
    The publication date of the object

Children
========

Displays the direct children (sub pages) of an object as a list. Here you can
bulk edit (change position, active state, etc.) or delete objects.

Images
======

The images tab handles the local images of the page.

Add Images
    Click the ``Select Images``-button and select the images you want to upload.

Update Images
    Change the data you want and click the ``Update``-button.

Delete Images
    Select the checkboxes beside the images you want to delete and click the
    ``Delete``-button.

Usage of images within content
------------------------------

There are two different ways to use the images:

1. Within the selected :ref:`template <template-label>`
2. Within the :term:`WYSIWYG` field of a content object
 
Files
=====

The files tab handles the local files of the page.

Add Files
    Click the ``Select File``-button and select the file you want to upload. Repeat
    that for all files and click ``Save Files``-button.

Update Files
    Change the data you want and click the ``Update``-button.

Delete Files
    Select the checkboxes beside the files you want to delete and click the
    ``Delete``-button.

Usage
-----

There are two different ways to use the files:

1. Within the selected :ref:`template <template-label>`
2. Within the :term:`WYSIWYG` field of a content object

Portlets
========

Here you can add portlets to an content object.

Blocked parent slots
    By default portlets are inherited from the parent content object or the
    :term:`portal`. If you want you can block this portlets per :term:`slot`.
    For that just select the checkbox beside the slot and click the
    ``Save Blocked Parent Slots``-button.

Slots
    Here you will find all assinged portlets per slot for this page. By default
    there is a left and a right slot.

Add a portlet
    To add a portlet, select the kind of portlet and click the ``Add Portlet``-button.
    Fill in ``position``, ``slot``, ``title`` and the specific portlet data and
    click the ``Save Portlet``-button.

Edit a portlet
    In order to edit a portlet, click on the ``Edit``-button of the existing
    portlet, change the data within the specific portlet form and click the
    ``Save Portlet``-button.

Delete a portlet
    Click on the ``Delete``-button of the portlet and answer the question with 
    ``yes``.

Comments
========

The comments tab manages the behaviour of commenting of the page.

Commentable
    This decides if commments are allowed for this page or not. There
    are three choices:

    * Default: The state is inherited from the parent object.

    * Yes: Comments are allowed.

    * No: Comments are disallowed.

Comments
    Displays all comments for this page. Here you can bulk edit (public, etc.) or
    delete comments.

SEO
===

Meta Keywords
    This field will be displayed as content attribute of the meta keywords tag.
    By default it displays the tags of the content object.

Meta description
    This field will be displayed as content attribute of the meta description tag.
    By default it displays the description of the content object.

Placeholders
------------

You can use several placeholders within both fields, which are:

<title>
    This includes the title of the content object.

<tags>
    This includes the tags of the content object.

<description>
    This includes the description of the content object.
