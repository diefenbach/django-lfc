from django.db import models

from django.db import models
from django.db.models.query import QuerySet

class BaseContentQuerySet(QuerySet):
    """Custom QuerySet for BaseContent.
    """
    def content_objects(self):
        """Returns a list of content objects. Should be used at the end of
        a QuerySet chain, e.g.::

            BaseContent.objects.filter(language="en").exclude(pk=1).content_objects()
        """
        result = []
        for obj in self.all():
            result.append(obj.get_content_object())

        return result

    def get(self, *args, **kwargs):
        """Returns the specific content object instead of the BaseContent
        object.
        """
        obj = super(BaseContentQuerySet, self).get(*args, **kwargs)
        return obj.get_content_object()

class BaseContentManager(models.Manager):
    """Custom manager for BaseContent.
    """
    def get_query_set(self):
        """Overwritten to return BaseContentQuerySet.
        """
        return BaseContentQuerySet(self.model)

    def restricted(self, request):
        """Returns a query set according to the permissions of the current
        user.
        """
        user = request.user
        if user and user.is_superuser:
            return self.get_query_set()
        else:
            return self.get_query_set().filter(active=True)