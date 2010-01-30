# django imports
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

# lfc imports
from lfc.models import Application
from lfc.utils import import_module

# Applications ##############################################################
def applications(request, template_name="lfc/manage/applications.html"):
    """Displays install/uninstall applications view.
    """
    applications = []
    for app_name in settings.INSTALLED_APPS:
        module = import_module(app_name)
        if hasattr(module, "install"):
            try:
                Application.objects.get(name=app_name)
            except Application.DoesNotExist:
                installed = False
            else:
                installed = True

            applications.append({
                "name" : app_name,
                "installed" : installed,
                "pretty_name" : getattr(module, "name", app_name),
                "description" : getattr(module, "description", None),
            })

    url = reverse("lfc_applications")
    return render_to_response(template_name, RequestContext(request, {
        "applications" : applications,
    }))

def install_application(request, name):
    """Installs LFC application with passed name.
    """
    import_module(name).install()
    try:
        Application.objects.create(name=name)
    except Application.DoesNotExist:
        pass

    url = reverse("lfc_applications")
    return HttpResponseRedirect(url)

def reinstall_application(request, name):
    """Reinstalls LFC application with passed name.
    """
    import_module(name).uninstall()
    import_module(name).install()
    try:
        Application.objects.create(name=name)
    except IntegrityError:
        pass

    url = reverse("lfc_applications")
    return HttpResponseRedirect(url)

def uninstall_application(request, name):
    """Uninstalls LFC application with passed name.
    """
    import_module(name).uninstall()

    try:
        application = Application.objects.get(name=name)
    except Application.DoesNotExist:
        pass
    else:
        application.delete()

    url = reverse("lfc_applications")
    return HttpResponseRedirect(url)

def application(request, name, template_name="lfc/manage/application.html"):
    """
    """
    url = reverse("lfc_application", kwargs={ "name" : name })
    return HttpResponseRedirect(url)
