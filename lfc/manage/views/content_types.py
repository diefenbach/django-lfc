# django imports
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

# lfc imports
from lfc.models import ContentTypeRegistration
from lfc.manage.forms import ContentTypeRegistrationForm

def content_types(request):
    """Redirects to the first content type.
    """
    ctr = ContentTypeRegistration.objects.filter()[0]
    url = reverse("lfc_content_type", kwargs={"id" : ctr.id })
    return HttpResponseRedirect(url)

def content_type(request, id, template_name="lfc/manage/content_types.html"):
    """ Displays the main screen of the content type management.
    """
    ctr = ContentTypeRegistration.objects.get(pk=id)

    if request.method == "POST":
        form = ContentTypeRegistrationForm(data = request.POST, instance=ctr)
        if form.is_valid():
            form.save()
    else:
        form = ContentTypeRegistrationForm(instance=ctr)

    return render_to_response(template_name, RequestContext(request, {
        "types" : ContentTypeRegistration.objects.all(),
        "ctr" : ctr,
        "form" : form,
    }))

