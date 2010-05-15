# portlets imports
from portlets.utils import register_portlet

# lfc imports
from lfc.utils.registration import register_template
from lfc.utils.registration import register_content_type
from lfc.models import NavigationPortlet
from lfc.models import Page
from lfc.models import PagesPortlet
from lfc.models import RandomPortlet
from lfc.models import TextPortlet

def initialize():
    """Registers default portlets, templates and content types.
    """
    # Portlets
    register_portlet(NavigationPortlet, "Navigation")
    register_portlet(PagesPortlet, "Pages")
    register_portlet(RandomPortlet, "Random")
    register_portlet(TextPortlet, "Text")

    # Register Templates
    register_template(name = "Plain", path="lfc/templates/plain.html")
    register_template(name = "Article", path="lfc/templates/article.html")
    register_template(name = "Gallery", path="lfc/templates/gallery.html", images_columns=3)
    register_template(name = "Overview", path="lfc/templates/overview.html")

    # Content Types
    register_content_type(
        Page,
        name="Page",
        sub_types=["Page"],
        templates=["Article", "Plain", "Gallery", "Overview"],
        default_template="Article")
