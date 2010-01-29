=======
Content
=======

.. warning::

    LFC is in alpha state. Please consider the API as supposed to be changed 
    until it reaches beta state.

.. autoclass:: lfc.models.Portal
    :members: are_comments_allowed, get_children, get_notification_emails,
      get_parent_for_portlets, get_template
     
.. autoclass:: lfc.models.BaseContent
    :members: are_comments_allowed, form, get_ancestors, get_ancestors_reverse, 
     get_canonical, get_content_object, get_descendants, get_image, 
     get_meta_keywords, get_meta_description, get_searchable_text, 
     get_template, get_title, get_translation, has_language, is_canonical, 
     is_translation, get_parent_for_portlets