# django imports
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.comments.signals import comment_was_posted
from django.core.mail import EmailMessage
from django.db.models.signals import post_save

# lfc imports
import lfc.signals
import lfc.utils
from lfc.models import BaseContent

def comment_was_posted_listener(sender, **kwargs):
    """Listen to order submitted signal
    """
    portal = lfc.utils.get_portal()
    site = Site.objects.get(id=settings.SITE_ID)
    comment = kwargs.get("comment")

    subject = "New Comment in %s" % portal.title
    from_email = portal.from_email
    to_emails = portal.get_notification_emails()

    body = "Name: %s\n" % comment.name
    body += "E-Mail: %s\n" % comment.email
    body += "URL: %s\n" % comment.url
    body += "Comment %s\n" % comment.comment
    body += "Comment URL: %s" % "http://" + site.domain + "admin/comments/comment/%s" % comment.id

    mail = EmailMessage(
        subject    = subject,
        body       = body,
        from_email = from_email,
        to         = to_emails
    )

    mail.send(fail_silently=True)

comment_was_posted.connect(comment_was_posted_listener)