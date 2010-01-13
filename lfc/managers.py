from django.db import models

class BaseContentManager(models.Manager):
    def get_query_set(self):
        from lfc.utils.middleware import get_current_user
        if get_current_user().is_superuser:
            return super(BaseContentManager, self).get_query_set()
        else:
            return super(BaseContentManager, self).get_query_set().filter(active=True)