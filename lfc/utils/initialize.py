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

# resources imports
import resources.utils
from resources.utils import register_resource 
from resources.config import CSS, JS

def initialize(create_resources=False):
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
    
    # Register Resources
    register_resource(type=CSS, group="lfc", path="lfc/yui/reset-fonts.css")
    register_resource(type=CSS, group="lfc", path="lfc/lightbox/css/jquery.lightbox-0.5.css")
    register_resource(type=CSS, group="lfc", path="lfc/blueprint/src/grid.css")
    register_resource(type=CSS, group="lfc", path="lfc_theme/css/tiny.css")
    register_resource(type=CSS, group="lfc", path="lfc_theme/css/lfc.css")

    register_resource(type=JS, group="lfc", path="lfc/jquery/jquery.min.js")
    register_resource(type=JS, group="lfc", path="lfc/jquery/jquery.tools.min.js")
    register_resource(type=JS, group="lfc", path="lfc/lightbox/js/jquery.lightbox-0.5.js")
    register_resource(type=JS, group="lfc", path="lfc_theme/js/lfctheme.js")

    register_resource(type=CSS, group="manage", path="lfc/yui/reset-min.css")
    register_resource(type=CSS, group="manage", path="lfc/lightbox/css/jquery.lightbox-0.5.css")
    register_resource(type=CSS, group="manage", path="lfc/jquery-ui-1.8.4.custom/css/smoothness/jquery-ui-1.8.4.custom.css")
    register_resource(type=CSS, group="manage", path="lfc/jquery/jquery.jgrowl.css")
    register_resource(type=CSS, group="manage", path="lfc/jquery/superfish/superfish.css")
    register_resource(type=CSS, group="manage", path="lfc/jquery/autocomplete/jquery.autocomplete.css")
    register_resource(type=CSS, group="manage", path="lfc/css/lfc_manage.css")
    register_resource(type=CSS, group="manage", path="lfc/swfupload/default.css")
    register_resource(type=CSS, group="manage", path="lfc/cleditor/jquery.cleditor.css")

    register_resource(type=JS, group="manage", path="/admin/jsi18n", merge=0, minify=0)
    register_resource(type=JS, group="manage", path="admin/js/core.js")
    register_resource(type=JS, group="manage", path="admin/js/calendar.js")
    register_resource(type=JS, group="manage", path="admin/js/urlify.js")
    register_resource(type=JS, group="manage", path="lfc/jquery/jquery-1.4.2.min.js")
    register_resource(type=JS, group="manage", path="lfc/cleditor/jquery.cleditor.min.js")
    register_resource(type=JS, group="manage", path="lfc/jquery/jquery.tools.min.js")
    register_resource(type=JS, group="manage", path="lfc/jquery/jquery.form.js")
    register_resource(type=JS, group="manage", path="lfc/jquery/jquery.jgrowl_minimized.js")
    register_resource(type=JS, group="manage", path="lfc/jquery/jquery.cookie.pack.js")
    register_resource(type=JS, group="manage", path="lfc/jquery/superfish/superfish.js")
    register_resource(type=JS, group="manage", path="lfc/jquery/jquery.ba-bbq.min.js")
    register_resource(type=JS, group="manage", path="lfc/jquery-ui-1.8.4.custom/js/jquery-ui-1.8.4.custom.min.js")
    register_resource(type=JS, group="manage", path="lfc/jquery/autocomplete/jquery.autocomplete.pack.js")
    register_resource(type=JS, group="manage", minify=0, path="lfc/swfupload/swfupload.js")
    register_resource(type=JS, group="manage", path="lfc/swfupload/swfupload.queue.js")
    register_resource(type=JS, group="manage", path="lfc/swfupload/fileprogress.js")
    register_resource(type=JS, group="manage", path="lfc/swfupload/handlers.js")
    register_resource(type=JS, group="manage", path="lfc/swfupload/swfupload.cookies.js")
    register_resource(type=JS, group="manage", path="lfc/js/lfc_manage.js")
    register_resource(type=JS, group="manage", path="lfc/js/lfc_editor.js")
    register_resource(type=JS, group="manage", merge=0, path="admin/js/admin/DateTimeShortcuts.js")

    if create_resources:    
        resources.utils.create_resources()
    
    # Content Types
    register_content_type(
        Page,
        name="Page",
        sub_types=["Page"],
        templates=["Article", "Plain", "Gallery", "Overview"],
        default_template="Article")
