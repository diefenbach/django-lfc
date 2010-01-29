==========================
Get specific content types
==========================

Situation
=========

All content types of LFC inherit from LFC's BaseContent type. In order
to get a list of all content types one could try to do::

    BaseContent.objects.all()

The problem with this is, that Django will deliever instances of BaseContent
(via a query set) and not, as you might expect, the specific content objects.

Approaches
==========

There are several ways to get around that:

1. Use the instance of a BaseContent to get the specific content type::

    from lfc.models import BaseContent

    obj = BaseContent.objects.get(pk=1)
    ct = obj.get_content_object()
    
   which is of course the same as::
   
     obj = BaseContent.objects.get(pk=1).get_content_object()
     
2. Use the ``get_content_objects`` method of the LFC specific query set::

        qs = BaseContent.objects.filter(pk=1)
        objs = qs.get_content_objects()

  As ``get_content_objects`` is a method of the query set you can use it at the
  **end** of the Django's common query set chains, e.g.: ::

        objs = BaseContent.objects.filter(pk=1).get_content_objects()
        objs = BaseContent.objects.restricted(request).filter(pk=1).get_content_objects()
        objs = BaseContent.objects.filter(langugae="en").exclude(pk=1).get_content_objects()

  Please note: ``get_content_objects`` itselfs returns a list of objects so you
  can't call query set methods on it.

3. Use the provided utility methods::

    import lfc.utils

    obj = lfc.utils.get_content_object(pk=1)
    objs = lfc.utils.get_content_objects(pk=1)

  You can also pass the request in order to take care of the current users'
  permissons::

    obj = lfc.utils.get_content_object(request, pk=1)
    objs = lfc.utils.get_content_objects(request, pk=1)
