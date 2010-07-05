# django imports
from django.core.management.base import BaseCommand

WELCOME_DESCRIPTION = """
<p>LFC is a CMS based on <a href="http://www.python.org/" target="_blank">Python</a>,
<a href="http://www.djangoproject.com/" target="_blank">Django</a> and
<a href="http://jquery.com/" target="_blank">jQuery</a>.</p>

<h1>Login</h1>
<p>Go to the <a href="/manage/">management interface</a> to start to add content.</p>

<h1>Information &amp; Help</h1>
<p>You can find more information and help on following places:</p>
<ul>
<li><a href="http://www.lfcproject.com" target="_blank">Official page</a></li>
<li><a href="http://packages.python.org/django-lfc/index.html" target="_blank">Documentation on PyPI</a></li>
<li><a href="http://pypi.python.org/pypi/django-lfc" target="_blank">Releases on PyPI</a></li>
<li><a href="http://bitbucket.org/diefenbach/django-lfc" target="_blank">Source code on bitbucket.org</a></li>
<li><a href="http://groups.google.com/group/django-lfc" target="_blank">Google Group</a></li>
<li><a href="http://twitter.com/lfcproject" target="_blank">lfsproject on Twitter</a></li>
<li><a href="irc://irc.freenode.net/django-lfc" target="_blank">IRC</a></li>
</ul>
"""

class Command(BaseCommand):
    args = ''
    help = 'Initializes LFC'

    def handle(self, *args, **options):

        # Portal
        from lfc.models import Portal
        portal = Portal.objects.create(id=1, title="LFC")

        # Roles & Permissions
        import permissions.utils

        # roles
        anonymous = permissions.utils.register_role("Anonymous")
        editor = permissions.utils.register_role("Editor")
        manager = permissions.utils.register_role("Manager")
        owner = permissions.utils.register_role("Owner")
        reader = permissions.utils.register_role("Reader")
        reviewer = permissions.utils.register_role("Reviewer")

        # permissions
        add_perm = permissions.utils.register_permission("Add", "add")
        delete_perm = permissions.utils.register_permission("Delete", "delete")
        edit_perm = permissions.utils.register_permission("Edit", "edit")
        submit_perm = permissions.utils.register_permission("Submit", "submit")
        view_perm = permissions.utils.register_permission("View", "view")
        manage_portal_perm = permissions.utils.register_permission("Manage portal", "manage_portal", [Portal])

        # portal permissions
        permissions.utils.grant_permission(portal, anonymous, view_perm)
        permissions.utils.grant_permission(portal, manager, add_perm)
        permissions.utils.grant_permission(portal, manager, delete_perm)
        permissions.utils.grant_permission(portal, manager, edit_perm)
        permissions.utils.grant_permission(portal, manager, manage_portal_perm)
        permissions.utils.grant_permission(portal, manager, view_perm)
        permissions.utils.grant_permission(portal, manager, submit_perm)
        permissions.utils.grant_permission(portal, owner, view_perm)
        permissions.utils.grant_permission(portal, owner, submit_perm)
        permissions.utils.grant_permission(portal, reader, view_perm)
        permissions.utils.grant_permission(portal, reviewer, view_perm)
        permissions.utils.grant_permission(portal, reviewer, submit_perm)

        # Workflows
        import workflows.utils
        from workflows.models import Workflow
        from workflows.models import State
        from workflows.models import Transition
        from workflows.models import WorkflowPermissionRelation 
        from workflows.models import StatePermissionRelation
        from workflows.models import StateInheritanceBlock
        from lfc.models import WorkflowStatesInformation

        # Plain Workflow #####################################################
        plain_workflow = Workflow.objects.create(name="Plain")

        private = State.objects.create(name="Private", workflow = plain_workflow)
        public = State.objects.create(name="Public", workflow = plain_workflow)

        WorkflowStatesInformation.objects.create(state=public, public=True)

        make_public = Transition.objects.create(name="Make public", workflow = plain_workflow, destination = public)
        make_private = Transition.objects.create(name="Make private", workflow = plain_workflow, destination = private)

        private.transitions.add(make_public)
        public.transitions.add(make_private)
        
        # Initial State
        plain_workflow.initial_state = private
        plain_workflow.save()
        
        # Workflow Permissions
        WorkflowPermissionRelation.objects.create(workflow=plain_workflow, permission=add_perm)
        WorkflowPermissionRelation.objects.create(workflow=plain_workflow, permission=delete_perm)
        WorkflowPermissionRelation.objects.create(workflow=plain_workflow, permission=edit_perm)
        WorkflowPermissionRelation.objects.create(workflow=plain_workflow, permission=view_perm)

        # State Permissions
        # Private
        StatePermissionRelation.objects.create(state=private, permission=add_perm, role=manager)
        StatePermissionRelation.objects.create(state=private, permission=delete_perm, role=manager)
        StatePermissionRelation.objects.create(state=private, permission=edit_perm, role=manager)
        StatePermissionRelation.objects.create(state=private, permission=view_perm, role=manager)

        StatePermissionRelation.objects.create(state=private, permission=add_perm, role=owner)
        StatePermissionRelation.objects.create(state=private, permission=delete_perm, role=owner)
        StatePermissionRelation.objects.create(state=private, permission=edit_perm, role=owner)
        StatePermissionRelation.objects.create(state=private, permission=view_perm, role=owner)

        StateInheritanceBlock.objects.create(state=private, permission=add_perm)
        StateInheritanceBlock.objects.create(state=private, permission=delete_perm)
        StateInheritanceBlock.objects.create(state=private, permission=edit_perm)
        StateInheritanceBlock.objects.create(state=private, permission=view_perm)

        # Public
        StateInheritanceBlock.objects.create(state=public, permission=add_perm)
        StateInheritanceBlock.objects.create(state=public, permission=delete_perm)
        StateInheritanceBlock.objects.create(state=public, permission=edit_perm)

        # Portal Workflow  ###################################################
        portal_workflow = Workflow.objects.create(name="Portal")
        
        # States
        private = State.objects.create(name="Private", workflow=portal_workflow)
        public = State.objects.create(name="Public", workflow=portal_workflow)
        submitted = State.objects.create(name="Submitted", workflow=portal_workflow)

        WorkflowStatesInformation.objects.create(state=public, public=True)
        WorkflowStatesInformation.objects.create(state=submitted, review=True)
        
        # Transitions
        make_public = Transition.objects.create(name="Make public", workflow = portal_workflow, destination = public)
        make_private = Transition.objects.create(name="Make private", workflow = portal_workflow, destination = private)
        submit = Transition.objects.create(name="Submit", workflow = portal_workflow, destination = submitted, permission=submit_perm)
        reject = Transition.objects.create(name="Reject", workflow = portal_workflow, destination = private)

        private.transitions.add(make_public)
        private.transitions.add(submit)
        public.transitions.add(make_private)
        submitted.transitions.add(make_public)
        submitted.transitions.add(reject)
        
        # Initial state
        portal_workflow.initial_state = private
        portal_workflow.save()
        
        # Permissions
        WorkflowPermissionRelation.objects.create(workflow=portal_workflow, permission=add_perm)
        WorkflowPermissionRelation.objects.create(workflow=portal_workflow, permission=delete_perm)
        WorkflowPermissionRelation.objects.create(workflow=portal_workflow, permission=edit_perm)
        WorkflowPermissionRelation.objects.create(workflow=portal_workflow, permission=view_perm)
        WorkflowPermissionRelation.objects.create(workflow=portal_workflow, permission=submit_perm)

        # State permissions
        
        # Private
        StatePermissionRelation.objects.create(state=private, permission=add_perm, role=manager)
        StatePermissionRelation.objects.create(state=private, permission=delete_perm, role=manager)
        StatePermissionRelation.objects.create(state=private, permission=edit_perm, role=manager)
        StatePermissionRelation.objects.create(state=private, permission=submit_perm, role=manager)
        StatePermissionRelation.objects.create(state=private, permission=view_perm, role=manager)

        StatePermissionRelation.objects.create(state=private, permission=add_perm, role=owner)
        StatePermissionRelation.objects.create(state=private, permission=delete_perm, role=owner)
        StatePermissionRelation.objects.create(state=private, permission=edit_perm, role=owner)
        StatePermissionRelation.objects.create(state=private, permission=submit_perm, role=owner)
        StatePermissionRelation.objects.create(state=private, permission=view_perm, role=owner)

        StateInheritanceBlock.objects.create(state=private, permission=add_perm)
        StateInheritanceBlock.objects.create(state=private, permission=delete_perm)
        StateInheritanceBlock.objects.create(state=private, permission=edit_perm)
        StateInheritanceBlock.objects.create(state=private, permission=submit_perm)
        StateInheritanceBlock.objects.create(state=private, permission=view_perm)

        # Public
        StatePermissionRelation.objects.create(state=public, permission=add_perm, role=manager)
        StatePermissionRelation.objects.create(state=public, permission=delete_perm, role=manager)
        StatePermissionRelation.objects.create(state=public, permission=edit_perm, role=manager)
        StatePermissionRelation.objects.create(state=public, permission=submit_perm, role=manager)
        StatePermissionRelation.objects.create(state=public, permission=view_perm, role=manager)

        StatePermissionRelation.objects.create(state=public, permission=view_perm, role=reader)

        StateInheritanceBlock.objects.create(state=public, permission=add_perm)
        StateInheritanceBlock.objects.create(state=public, permission=delete_perm)
        StateInheritanceBlock.objects.create(state=public, permission=edit_perm)
        StateInheritanceBlock.objects.create(state=public, permission=submit_perm)

        # Submitted
        StatePermissionRelation.objects.create(state=submitted, permission=add_perm, role=manager)
        StatePermissionRelation.objects.create(state=submitted, permission=delete_perm, role=manager)
        StatePermissionRelation.objects.create(state=submitted, permission=edit_perm, role=manager)
        StatePermissionRelation.objects.create(state=submitted, permission=submit_perm, role=manager)
        StatePermissionRelation.objects.create(state=submitted, permission=view_perm, role=manager)

        StatePermissionRelation.objects.create(state=submitted, permission=add_perm, role=reader)
        StatePermissionRelation.objects.create(state=submitted, permission=delete_perm, role=reader)
        StatePermissionRelation.objects.create(state=submitted, permission=edit_perm, role=reader)
        StatePermissionRelation.objects.create(state=submitted, permission=submit_perm, role=reader)
        StatePermissionRelation.objects.create(state=submitted, permission=view_perm, role=reader)
        StatePermissionRelation.objects.create(state=submitted, permission=view_perm, role=owner)
        
        StateInheritanceBlock.objects.create(state=submitted, permission=add_perm)
        StateInheritanceBlock.objects.create(state=submitted, permission=delete_perm)
        StateInheritanceBlock.objects.create(state=submitted, permission=edit_perm)
        StateInheritanceBlock.objects.create(state=submitted, permission=view_perm)
        StateInheritanceBlock.objects.create(state=submitted, permission=submit_perm)

        # Portlets
        from portlets.models import Slot
        from portlets.models import PortletAssignment

        left_slot = Slot.objects.create(name="Left")
        right_slot = Slot.objects.create(name="Right")

        # Registration
        from lfc.utils.registration import register_content_type
        from lfc.utils.registration import register_template
        from portlets.utils import register_portlet
        from lfc.models import Page

        # Register portlets
        from lfc.models import NavigationPortlet, PagesPortlet, RandomPortlet, TextPortlet

        register_portlet(NavigationPortlet, "Navigation")
        register_portlet(PagesPortlet, "Pages")
        register_portlet(RandomPortlet, "Random")
        register_portlet(TextPortlet, "Text")

        # Register templates
        register_template(name = "Plain", path="lfc/templates/plain.html")
        register_template(name = "Article", path="lfc/templates/article.html")
        register_template(name = "Gallery", path="lfc/templates/gallery.html", images_columns=3)
        register_template(name = "Overview", path="lfc/templates/overview.html")

        register_content_type(Page, "Page", sub_types=["Page"], templates=["Article", "Gallery", "Overview", "Plain"], default_template="Article", workflow="Plain")

        # Page
        page = Page.objects.create(title="Welcome to LFC", slug="welcome-to-lfc", text=WELCOME_DESCRIPTION)
        workflows.utils.set_state(page, public)


def create_plain_workflow():
    w = Workflow.objects.create(name="Plain")

    private = State.objects.create(name="Private", workflow= w)
    public = State.objects.create(name="Public", workflow= w)

    make_public = Transition.objects.create(name="Make public", workflow=w, destination = public)
    make_private = Transition.objects.create(name="Make private", workflow=w, destination = private)

    private.transitions.add(make_public)
    public.transitions.add(make_private)

    w.initial_state = private
    w.save()