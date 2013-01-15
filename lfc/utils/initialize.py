# portlets imports
from portlets.utils import register_portlet

# lfc imports
from lfc.utils.registration import register_template
from lfc_portlets.models import NavigationPortlet
from lfc_portlets.models import ContentPortlet
from lfc_portlets.models import RandomPortlet
from lfc_portlets.models import TextPortlet


def initialize():
    """Registers default portlets, templates and content types.
    """
    # Portlets
    register_portlet(NavigationPortlet, "Navigation")
    register_portlet(ContentPortlet, "Pages")
    register_portlet(RandomPortlet, "Random")
    register_portlet(TextPortlet, "Text")

    # Register Templates
    register_template(name="Plain", path="lfc/templates/plain.html")
    register_template(name="Article", path="lfc/templates/article.html")
    register_template(name="Gallery", path="lfc/templates/gallery.html", images_columns=3)
    register_template(name="Overview", path="lfc/templates/overview.html")
