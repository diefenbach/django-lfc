========
Settings
========

Django settings
===============

The following are default `Django settings <http://docs.djangoproject.com/en/1.2/ref/settings>`_
which are important for LFC.

EMAIL_HOST
    
    The host to use for sending e-mail.
    
EMAIL_HOST_USER

    Username to use for the SMTP server defined in EMAIL_HOST. If empty, 
    Django won't attempt authentication.
    
EMAIL_HOST_PASSWORD

    Password to use for the SMTP server defined in EMAIL_HOST. This setting 
    is used in conjunction with EMAIL_HOST_USER when authenticating to the 
    SMTP server. If either of these settings is empty, Django won't attempt 
    authentication.

LANGUAGE_CODE

    This defines the default language for LFC, e.g.::

        LANGUAGE_CODE = 'en'

LANGUAGES

    This defines all available languages within LFC, the format is::

        LANGUAGES = (
            ("en", _(u"English")),
            ("de", _(u"German")),
        )

LFC settings
============

LFC_MANAGE_WORKFLOWS

    If True the management screens for workflows are displayed within LFC's 
    management interface.
    
LFC_MANAGE_PERMISSIONS

    If True the management screens for permissions are displayed within LFC's 
    management interface.

LFC_MANAGE_APPLICATIONS

    If True the management screens for applications are displayed within LFC's 
    management interface.

LFC_MANAGE_USERS

    If True the management screens for users are displayed within LFC's 
    management interface.
