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
    register_portlet(NavigationPortlet, u"Navigation")
    register_portlet(ContentPortlet, u"Content")
    register_portlet(RandomPortlet, u"Random")
    register_portlet(TextPortlet, u"Text")

    # Register Templates
    register_template(name=u"Plain", path=u"lfc/templates/plain.html")
    register_template(name=u"Article", path=u"lfc/templates/article.html")
    register_template(name=u"Gallery", path=u"lfc/templates/gallery.html", images_columns=3)
    register_template(name=u"Overview", path=u"lfc/templates/overview.html")
