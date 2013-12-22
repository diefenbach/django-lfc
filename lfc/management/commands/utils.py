# encoding: utf-8

# permissions imports
import permissions.utils


WELCOME_DESCRIPTION = """
<p>LFC is a CMS based on <a href="http://www.python.org/" target="_blank">Python</a>,
<a href="http://www.djangoproject.com/" target="_blank">Django</a> and
<a href="http://jquery.com/" target="_blank">jQuery</a>.</p>

<h2 class="middle-heading">Manage content</h2>
<p>Go to the <a href="/manage/">management interface</a> in order to manage content.</p>

<h2 class="middle-heading">Information &amp; Help</h2>
<p>You can find more information and help on following places:</p>
<ul>
<li><a href="http://www.lfcproject.com" target="_blank">Official page</a></li>
<li><a href="http://packages.python.org/django-lfc/index.html" target="_blank">Documentation</a></li>
<li><a href="http://pypi.python.org/pypi/django-lfc" target="_blank">Releases</a></li>
<li><a href="http://bitbucket.org/diefenbach/django-lfc" target="_blank">Source code</a></li>
<li><a href="http://groups.google.com/group/django-lfc" target="_blank">Google Group</a></li>
<li><a href="http://twitter.com/lfcproject" target="_blank">Twitter</a></li>
<li><a href="irc://irc.freenode.net/django-lfc" target="_blank">IRC</a></li>
</ul>
"""

def create_extended_permissions():
    manage_applications = permissions.utils.register_permission("Manage Applications", "manage_applications")
    manage_groups = permissions.utils.register_permission("Manage Groups", "manage_groups")
    manage_reviews = permissions.utils.register_permission("Manage Reviews", "manage_reviews")
    manage_roles = permissions.utils.register_permission("Manage Roles", "manage_roles")
    manage_users = permissions.utils.register_permission("Manage Users", "manage_users")
    manage_workflows = permissions.utils.register_permission("Manage Workflows", "manage_workflows")
    manage_content_types = permissions.utils.register_permission("Manage Content Types", "manage_content_types")
    manage_installations = permissions.utils.register_permission("Manage Installations", "manage_installations")
    manage_utils = permissions.utils.register_permission("Manage Utils", "manage_utils")

    return (manage_applications, manage_content_types, manage_groups,  manage_installations, manage_reviews, manage_roles, manage_users, manage_utils, manage_workflows)
