# python imports
from optparse import make_option

# django imports
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

# lfc imports
from lfc.models import Application
from lfc.models import Portal
from lfc.models import WorkflowStatesInformation

# lfc_page imports
from lfc_page.models import Page

# portlets import
from portlets.models import Slot

# workflows import
import workflows.utils
from workflows.models import State
from workflows.models import StateInheritanceBlock
from workflows.models import Transition
from workflows.models import Workflow
from workflows.models import WorkflowPermissionRelation

# permissions imports
import permissions.utils

# utils imports
from lfc.utils import import_module
from lfc.utils.initialize import initialize
from utils import WELCOME_DESCRIPTION


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--with-extended-permissions",
            action="store_true",
            dest="with_extended_permissions",
            default=False,
            help="Create extended permissions like manage_users, etc."
        ),
    )

    args = ''
    help = """Initializes LFC

    This will create default portlets, templates, content types and a simple
    workflow.

    This should be used to initialize the database to used for simple pages."""

    def handle(self, *args, **options):

        # Check whether the initialization has already be done
        try:
            Portal.objects.all()[0]
        except IndexError:
            pass
        else:
            print "Initialization has already be done."
            return

        initialize()

        # Register site
        site = Site.objects.all()[0]
        site.name = site.domain = "www.example.com"
        site.save()

        # Create portal
        portal = Portal.objects.create()

        # Register roles
        anonymous = permissions.utils.register_role("Anonymous")

        # Registers permissions
        view = permissions.utils.register_permission("View", "view")

        if options["with_extended_permissions"]:
            manage_applications, manage_content_types, manage_groups,  manage_installations, manage_reviews, manage_roles, manage_users, manage_utils, manage_workflows = create_extended_permissions()

        # Create slots
        left_slot, created = Slot.objects.get_or_create(name="Left")
        right_slot, created = Slot.objects.get_or_create(name="Right")

        # Set permissions for portal
        permissions.utils.grant_permission(portal, anonymous, "view")

        # Simple Workflow
        ##########################################################################

        # Add workflow
        workflow, created = Workflow.objects.get_or_create(name="Simple")

        # Add states
        private = State.objects.create(name="Private", workflow=workflow)
        public = State.objects.create(name="Public", workflow=workflow)

        # Create transitions
        make_public = Transition.objects.create(name="Make public", workflow=workflow, destination=public)
        make_private = Transition.objects.create(name="Make private", workflow=workflow, destination=private)

        # Add transitions
        private.transitions.add(make_public)
        public.transitions.add(make_private)

        # Add all permissions which are managed by the workflow
        WorkflowPermissionRelation.objects.create(workflow=workflow, permission=view)

        # Add permissions for single states
        # Private
        StateInheritanceBlock.objects.create(state=private, permission=view)

        # Define public state
        WorkflowStatesInformation.objects.create(state=public, public=True)

        # Define initial state
        workflow.initial_state = private
        workflow.save()

        # Set workflow for Page
        ctype = ContentType.objects.get_for_model(Page)
        workflows.utils.set_workflow_for_model(ctype, workflow)

        # Welcome Page
        page = Page.objects.create(title="Welcome to LFC", slug="welcome-to-lfc", text=WELCOME_DESCRIPTION)
        workflows.utils.set_state(page, public)

        portal.standard = page
        portal.save()

        import_module("lfc_page").install()
        try:
            Application.objects.create(name="lfc_page")
        except Application.DoesNotExist:
            pass

