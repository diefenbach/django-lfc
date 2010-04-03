from django.contrib import admin

from lfc.models import BaseContent
from lfc.models import ContentTypeRegistration
from lfc.models import Page
from lfc.models import Portal
from lfc.models import Image
from lfc.models import File
from lfc.models import NavigationPortlet
from lfc.models import PagesPortlet
from lfc.models import Template
from lfc.models import WorkflowStatesInformation

admin.site.register(ContentTypeRegistration)
admin.site.register(File)
admin.site.register(Image)
admin.site.register(Page)
admin.site.register(BaseContent)
admin.site.register(Portal)
admin.site.register(NavigationPortlet)
admin.site.register(PagesPortlet)
admin.site.register(Template)
admin.site.register(WorkflowStatesInformation)
