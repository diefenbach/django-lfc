from django.db import models

class BaseContentManager(models.Manager):
    """
    """
    def restricted(self, request):
        """
        """
        user = request.user
        if user and user.is_superuser:
            return self.get_query_set()
        else:
            return self.get_query_set().filter(active=True)