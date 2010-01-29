==========================
Get specific content types
==========================

Situation
=========

All content types of LFC inherit from LFC's BaseContent type. In order
to get a list of all content types one would do::

    BaseContent.objects.all()

The problem with this is, that Django will deliever instances of BaseContent
and not, as you might expect, the specific content objects.

Solutions
=========

There are several ways to get around that:

1. Use the instance of a BaseContent to get the specific content type::

    from lfc.models import BaseContent

    obj = BaseContent.objects.get(pk=1)
    ct = obj.get_content_object()

2. Use the LFC specific method ``get_content_objects`` of the LFC query set::

    qs = BaseContent.objects.filter(pk=1)
    objs = qs.get_content_objects()

  Here you can use the LFC specific restricted method of the manager::

        objs = BaseContent.objects.restricted(request).filter(pk=1).get_content_objects()

  you can do also of course::

        objs = BaseContent.objects.filter(pk=1).get_content_objects()
        objs = BaseContent.objects.restricted(request).filter(pk=1).get_content_objects()

  Generally you can use ``get_content_objects`` at the **end** of every query
  set chain but please note that ``get_content_objects`` do not return a query set
  itself but a list of specific content objects.

3. Use utility methods::

    import lfc.utils

    obj = lfc.utils.get_content_object(pk=1)
    objs = lfc.utils.get_content_objects(pk=1)

  You can also pass the request in order to take care of the current users
  permissons::

    obj = lfc.utils.get_content_object(request, pk=1)
    objs = lfc.utils.get_content_objects(request, pk=1)
