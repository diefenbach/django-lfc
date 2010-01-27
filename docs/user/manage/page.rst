====
Page
====

Data
=====

**Title**

The title of the page.

The title is displayed on top of the page and as within the title tab of the
page.

**Display Title**

When this is checked the title is displayed on top of the page.

**Slug**

The unique URL of the page within the parent page.

**Description**

The description of the page.

This is used within the overview template and search results.

**Text**

The main HTML text of a page.

**Tags**

The tags of the page.

Tags are keywords. This kind of metadata helps describe a page and allows it
to be found again by browsing or searching.

Metadata
========

.. _template-label:

**Template**

The template which is used to display the object's content. 

If this field is not displayed for this content object just the default 
template has been registered.

.. _page-standard-label:

**Standard**

The sub page which should be displayed if the page is viewed.

If this field is not displayed the page has no sub pages.

**Active**

Only active objects are displayed. If an user tries to display an inactive
objects he gets a page not found disclaimer (404).

**Exclude from navigation**

If checked this object is not displayed within the tabs or the navigation
portlet.

**Exclude from search results**

If checked this object is not displayed within search results.

**Language**

The language of the object.

If this field is not displayed your site has not multi languages.

**Publication date**

The publication date of the object

Children
========

Displays the direct children (sub pages) of an object as a list. Here one can 
bulk edit (change position, active state, etc.) or delete objects.

Images
======

The images tab handles the images of the page. These images are local 
images of the image.

**Add Images**

Click the ``Select Images``-button and select the images you want to upload.

**Update Images**

Change the data you want and click the ``Update``-button.

**Delete Images**

Select the checkboxes beside the images you want to delete and click the
``Delete``-button.

**Usage of images within content**

There are two different ways to use the images:

1. Within the selected :ref:`template <template-label>`

   The images are displayed dependend on the selected template, e.g.:
   
        - "Article"
           The first image is displayed on top left of the page. All others 
           are ignored.
           
        - "Gallery"
           All images are displayed as a 3 x 3 grid.

2. Within the text field of the content object

        1. Within the WYSIWYG editor click on the image button.
        2. Besided the ``Image URL`` field click on the ``Browse`` button 
           and select an image in the size you need it. Fill in ``Image 
           Description`` and ``Title`` and click the "Insert"-button.
           
Files
=====

The files tab handles the files of the page. These files are local
files of the page.

**Add Files**

Click the ``Select File``-button and select the file you want to upload. Repeat
that for all files and click ``Save Files``-button.

**Update Files**

Change the data you want and click the ``Update``-button.

**Delete Files**

Select the checkboxes beside the files you want to delete and click the
``Delete``-button.

**Usage**

There are two different ways to use the files:

1. Within the selected :ref:`template <template-label>`

   The files are displayed dependend on the selected template, e.g.:

        At the moment there is no template which supports files.

2. Within the text field of the content object

        1. Within the WYSIWYG editor select some text and click on the 
           ``insert/edit link``-button.
        2. Besided the ``Link URL`` field click on the ``Browse``-button
           and select a file you want to link to and optionally add a title.
        3. Click the ``Insert``-button.

Portlets
========

Here one can add portlets to a page.

:term:`Portlets` a pieces of content which are displayed in :term:`Slots` left
and right of your page.

**Blocked parent slots**

By default portlets are inherited from the parent page or the :term:`portal`.
I you want you can block this portlets per :term:`slot`. For that just select 
the checkbox beside the slot and click the ``Save Blocked Parent Slots``-button.

**Slots**

Here you will find all assinged portlets per slot for this page. By default 
there is a left and a right slot.

**Add a portlet**

To add a portlet, select the kind of portlet and click the ``Add Portlet``-button
Fill in ``position``, ``slot``, ``title`` and the specific portlet data and
click the ``Save Portlet``-button.

**Edit a portlet**

In order to edit a portlet, click on the ``Edit``-button of the existing 
portlet, change the data within the specific portlet form and click the 
``Save Portlet``-button.

**Delete a portlet**

Click on the ``Delete``-button of the portlet and answer the question with yes.

Comments
========

Handles the comments of the page.

**Commentable**

Here one can decide whether commments are allowed for this page or not. There
are three choices:

* default
  
  The state is inherited from the parent object

* Yes
  
  Comments are allowed

* No
  
  Comments are disallowed

**Comments**

Displays all comments for this page. Here one can bulk edit (public, etc.) or
delete comments.

SEO
===

**Meta Keywords**

This field will be displayed as content attribute of the meta keywords tag. 
By default it displays the tags of the content object.

**Meta description**

This field will be displayed as content attribute of the meta description tag. 
By default it displays the description of the content object.

**Placeholders**

One can use several placeholders within both fields, which are: 

- <title>

  This includes the title of the content object.

- <tags>

  This includes the tags of the content object.

- <description>

  This includes the description of the content object.
