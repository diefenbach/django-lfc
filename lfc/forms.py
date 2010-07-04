# contact_form imports
from contact_form.forms import ContactForm as BaseContactForm

# lfc imports
import lfc.utils

class ContactForm(BaseContactForm):
    """Specific ContactForm for LFC.
    """
    def __init__(self, data=None, files=None, request=None, *args, **kwargs):
        super(ContactForm, self).__init__(data=data, files=files, request=request, *args, **kwargs)
        self.portal = lfc.utils.get_portal()
        
    def from_email(self):
        return self.portal.from_email

    def recipient_list(self):
        return self.portal.get_notification_emails()