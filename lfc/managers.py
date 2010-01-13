from django.db import models

class BaseContentManager(models.Manager):
    def get_query_set(self):
        from lfc.utils.middleware import get_current_user
        user = get_current_user()
        if user and user.is_superuser:
            return super(BaseContentManager, self).get_query_set()
        else:
            return super(BaseContentManager, self).get_query_set().filter(active=True)