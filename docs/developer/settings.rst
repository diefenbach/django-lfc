========
Settings
========

Django settings
===============

The following are default `Django settings <https://docs.djangoproject.com/en/1.6/ref/settings>`_
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

LFC_MANAGE_APPLICATIONS

    If ``True`` the management screens for ``Applications`` are displayed within
    LFC's management interface. Default is ``True``.

LFC_MANAGE_CHILDREN

    If ``True`` the ``Children`` tabs are displayed within LFC's management
    interface. Default is ``True``.

LFC_MANAGE_COMMENTS

    If ``True`` the ``Comments`` tabs are displayed within LFC's
    management interface. Default is ``True``.

LFC_MANAGE_FILES

    If ``True`` the Files tabs are displayed within LFC's management interface.
    Default is ``True``.

LFC_MANAGE_HISTORY

    If ``True`` the history tab for the content objects are displayed within
    LFC's management interface. Default is ``True``.

LFC_MANAGE_IMAGES

    If ``True`` the ``Images`` tabs are displayed within LFC's management
    interface. Default is ``True``.

LFC_MANAGE_META_DATA

    If ``True`` the meta data tabs are displayed within LFC's management interface.
    Default is ``True``.

LFC_MANAGE_PERMISSIONS

    If ``True`` the ``Permissions`` tabs are displayed within LFC's management
    interface. Default is ``True``.

LFC_MANAGE_PORTLETS

    If ``True`` the ``Portlets`` tabs are displayed within LFC's management
    interface. Default is ``True``.

LFC_MANAGE_SEO

    If ``True`` the ``SEO`` tab for the portal and the content objects are
    displayed within LFC's management interface. Default is ``True``.

LFC_MANAGE_USERS

    If ``True`` the management screens for users, groups and roles are displayed
    within LFC's management interface. Default is ``True``.

LFC_MANAGE_UTILS

    If ``True`` the management screens for utils are displayed. Default is ``True``.

LFC_MANAGE_WORKFLOWS

    If ``True`` the management screens for workflows are displayed within LFC's
    management interface. Default is ``True``.

LFC_MULTILANGUAGE

    If ``True`` the management screens for translations and languages are
    displayed. Default is: ``len(LANGUAGES) > 1``.


LFC THEME settings
==================

LFC_THEME_WIDTH_SLOT_LEFT, LFC_THEME_WIDTH_SLOT_RIGHT

    Changes the width of the left and right slot. Default is 5 units for each
    slot.

    .. note:: The lfc-theme is based on a CSS grid (`<http://www.blueprintcss.org>`_).
              The total width of the grid is 24 units. Based on these settings,
              the width of the content is calculated automatically.
