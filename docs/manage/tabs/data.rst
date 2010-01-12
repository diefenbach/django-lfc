=====
Data
=====

Title
=====

The title of the page. 

The title is displayed on top of the page and as within the title tab of the 
page.

Display Title
=============

Only when this is checked the title is displayed on top of the page.

Slug
====

The unique URL of the page within the parent page.

Description
===========

The description of the page.

This is used within the overview template and search results.

Text
====

The HTML text of a page.

You can use several tags within this field:

page
----

Renders several fields of a specific page.

**Usage**::

{% page "url" "title|text" %}

**Example**::

    {% page "information/imprint" "text" %}

rss
---

Displays an RSS-feed

**Usage**::

{% rss "url" limit %}

**Example**::

    {% rss "http://twitter.com/statuses/user_timeline/7766902.rss" 5 %}
    
Tags
====

The tags of the page.