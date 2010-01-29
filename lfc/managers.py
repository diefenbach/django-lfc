from django.db import models

from django.db import models
from django.db.models.query import QuerySet

class BaseContentQuerySet(QuerySet):
    """Custom QuerySet for BaseContent.
    """
    def get_content_objects(self):
        """Returns a list of content objects. Should be used at the end of
        a QuerySet chain, e.g.::

            BaseContent.objects.filter(language="en").exclude(pk=1).get_content_objects()
        """
        result = []
        for obj in self.all():
            result.append(obj.get_content_object())

        return result

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